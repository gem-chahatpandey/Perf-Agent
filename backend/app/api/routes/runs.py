from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.models.run import RunCreate, RunMetadata, RunStatus
from app.storage.filesystem import storage
from app.core.security import get_current_user

router = APIRouter()


@router.post("/runs", status_code=201)
async def create_run(body: RunCreate, _user: str = Depends(get_current_user)):
    key = f"runs/{body.run_id}/metadata.json"
    if await storage.exists(key):
        raise HTTPException(400, f"Run {body.run_id} already exists")

    metadata = RunMetadata(
        run_id=body.run_id,
        name=body.name or body.run_id,
        description=body.description,
    )
    await storage.save(key, metadata.model_dump())
    return metadata.model_dump()


@router.get("/runs")
async def list_runs(_user: str = Depends(get_current_user)):
    items = await storage.list("runs")
    runs = []
    for item in items:
        try:
            meta = await storage.load(f"{item}/metadata.json")
            runs.append(meta)
        except (FileNotFoundError, Exception):
            continue
    runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return {"runs": runs, "total": len(runs)}


@router.get("/runs/{run_id}")
async def get_run(run_id: str, _user: str = Depends(get_current_user)):
    try:
        meta = await storage.load(f"runs/{run_id}/metadata.json")
        return meta
    except FileNotFoundError:
        raise HTTPException(404, f"Run {run_id} not found")
