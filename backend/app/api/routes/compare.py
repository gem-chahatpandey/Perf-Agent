from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from app.storage.filesystem import storage
from app.models.performance import PerformanceMetrics
from app.core.security import get_current_user

router = APIRouter()


class CompareRequest(BaseModel):
    run_ids: list[str]


@router.post("/runs/compare")
async def compare_runs(body: CompareRequest, _user: str = Depends(get_current_user)):
    if len(body.run_ids) < 2:
        raise HTTPException(400, "At least 2 run IDs required for comparison")

    results = {}
    for rid in body.run_ids:
        try:
            metrics = await storage.load(f"runs/{rid}/metrics.json")
            analysis = await storage.load(f"runs/{rid}/analysis.json")
            results[rid] = {"metrics": metrics, "analysis": analysis}
        except FileNotFoundError:
            raise HTTPException(404, f"Run {rid} data not found")

    comparison = _build_comparison(body.run_ids, results)
    return comparison


def _build_comparison(run_ids: list[str], results: dict) -> dict:
    rows = []
    for rid in run_ids:
        m = results[rid]["metrics"]
        a = results[rid]["analysis"]
        txns = m.get("transactions", [])
        avg_p95 = sum(t.get("p95_ms", 0) for t in txns) / max(len(txns), 1)
        rows.append({
            "run_id": rid,
            "total_transactions": m.get("total_transactions", 0),
            "error_rate_pct": m.get("overall_error_rate_pct", 0),
            "avg_p95_ms": round(avg_p95, 1),
            "peak_users": m.get("peak_concurrent_users", 0),
            "findings_count": a.get("total_findings", 0),
            "critical_findings": a.get("critical_count", 0),
        })

    deltas = []
    if len(rows) >= 2:
        r1, r2 = rows[0], rows[1]
        for metric in ("error_rate_pct", "avg_p95_ms", "findings_count"):
            v1, v2 = r1[metric], r2[metric]
            change = ((v2 - v1) / v1 * 100) if v1 != 0 else 0
            deltas.append({"metric": metric, "run1": v1, "run2": v2, "change_pct": round(change, 1)})

    return {"run_ids": run_ids, "runs": rows, "deltas": deltas}
