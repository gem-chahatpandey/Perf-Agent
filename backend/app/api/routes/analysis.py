from fastapi import APIRouter, HTTPException, Depends
from app.storage.filesystem import storage
from app.models.performance import PerformanceMetrics, SLAThresholds
from app.services.analysis.engine import PerformanceAnalyzer
from app.core.security import get_current_user

router = APIRouter()


@router.post("/runs/{run_id}/analyze")
async def run_analysis(run_id: str, _user: str = Depends(get_current_user)):
    return await analyze_run(run_id)


async def analyze_run(run_id: str) -> dict:
    if not await storage.exists(f"runs/{run_id}/metadata.json"):
        raise HTTPException(404, f"Run {run_id} not found")

    metrics_list = []
    for source in ("loadrunner", "appdynamics"):
        try:
            data = await storage.load(f"runs/{run_id}/{source}.json")
            metrics_list.append(PerformanceMetrics(**data))
        except FileNotFoundError:
            continue

    if not metrics_list:
        raise HTTPException(400, "No performance data uploaded for this run")

    combined = _merge_metrics(metrics_list, run_id)
    await storage.save(f"runs/{run_id}/metrics.json", combined.model_dump())

    analyzer = PerformanceAnalyzer()
    result = analyzer.analyze(combined)

    await storage.save(f"runs/{run_id}/analysis.json", result.model_dump())

    meta = await storage.load(f"runs/{run_id}/metadata.json")
    meta["analysis_completed"] = True
    meta["status"] = "completed"
    await storage.save(f"runs/{run_id}/metadata.json", meta)

    return result.model_dump()


@router.get("/runs/{run_id}/metrics")
async def get_metrics(run_id: str, _user: str = Depends(get_current_user)):
    try:
        return await storage.load(f"runs/{run_id}/metrics.json")
    except FileNotFoundError:
        raise HTTPException(404, "Merged metrics not found. Upload both reports or run analysis first.")


@router.get("/runs/{run_id}/analysis")
async def get_analysis(run_id: str, _user: str = Depends(get_current_user)):
    try:
        return await storage.load(f"runs/{run_id}/analysis.json")
    except FileNotFoundError:
        raise HTTPException(404, "Analysis not found. Run POST /runs/{run_id}/analyze first.")


def _merge_metrics(metrics_list: list[PerformanceMetrics], run_id: str) -> PerformanceMetrics:
    if len(metrics_list) == 1:
        return metrics_list[0]

    combined = PerformanceMetrics(run_id=run_id, source="combined")
    for m in metrics_list:
        combined.transactions.extend(m.transactions)
        combined.infrastructure.extend(m.infrastructure)
        combined.total_transactions += m.total_transactions
        combined.total_errors += m.total_errors
        if m.peak_concurrent_users > combined.peak_concurrent_users:
            combined.peak_concurrent_users = m.peak_concurrent_users
        if m.duration_seconds > combined.duration_seconds:
            combined.duration_seconds = m.duration_seconds
        if not combined.application and m.application:
            combined.application = m.application

    if combined.total_transactions > 0:
        combined.overall_error_rate_pct = combined.total_errors / combined.total_transactions * 100
    return combined
