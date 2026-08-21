from fastapi import APIRouter, HTTPException, Depends
from app.storage.filesystem import storage
from app.models.analysis import AnalysisResult
from app.services.rca.service import rca_service
from app.core.security import get_current_user

router = APIRouter()


@router.post("/runs/{run_id}/rca")
async def run_rca(run_id: str, _user: str = Depends(get_current_user)):
    return await perform_rca(run_id)


async def perform_rca(run_id: str) -> dict:
    try:
        analysis_data = await storage.load(f"runs/{run_id}/analysis.json")
    except FileNotFoundError:
        raise HTTPException(400, "Run analysis first before requesting RCA")

    analysis = AnalysisResult(**analysis_data)
    result = await rca_service.perform_rca(run_id, analysis)

    await storage.save(f"runs/{run_id}/rca.json", result.model_dump())

    meta = await storage.load(f"runs/{run_id}/metadata.json")
    meta["rca_completed"] = True
    await storage.save(f"runs/{run_id}/metadata.json", meta)

    return result.model_dump()


@router.get("/runs/{run_id}/rca")
async def get_rca(run_id: str, _user: str = Depends(get_current_user)):
    try:
        return await storage.load(f"runs/{run_id}/rca.json")
    except FileNotFoundError:
        raise HTTPException(404, "RCA not found. Run POST /runs/{run_id}/rca first.")
