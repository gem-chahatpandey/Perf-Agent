import re
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from app.storage.filesystem import storage
from app.parsers.loadrunner import LoadRunnerParser
from app.parsers.appdynamics import AppDynamicsParser
from app.core.security import get_current_user
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

ALLOWED_EXTENSIONS = {".csv", ".json", ".xml", ".txt", ".html", ".log"}
FILENAME_PATTERN = re.compile(r"^[\w\-. ]+$")
MAX_SIZE = settings.max_upload_size_mb * 1024 * 1024


@router.post("/runs/{run_id}/upload/loadrunner")
async def upload_loadrunner(run_id: str, file: UploadFile = File(...), _user: str = Depends(get_current_user)):
    return await _handle_upload(run_id, file, "loadrunner")


@router.post("/runs/{run_id}/upload/appdynamics")
async def upload_appdynamics(run_id: str, file: UploadFile = File(...), _user: str = Depends(get_current_user)):
    return await _handle_upload(run_id, file, "appdynamics")


@router.post("/runs/{run_id}/upload")
async def upload_reports(
    run_id: str,
    loadrunner_file: UploadFile = File(...),
    appdynamics_file: UploadFile = File(...),
    _user: str = Depends(get_current_user),
):
    loadrunner = await _process_upload(run_id, loadrunner_file, "loadrunner")
    appdynamics = await _process_upload(run_id, appdynamics_file, "appdynamics")

    return {
        "status": "success",
        "run_id": run_id,
        "uploads": [loadrunner, appdynamics],
    }


async def _handle_upload(run_id: str, file: UploadFile, source: str):
    return await _process_upload(run_id, file, source)


async def _process_upload(run_id: str, file: UploadFile, source: str) -> dict:
    if not await storage.exists(f"runs/{run_id}/metadata.json"):
        raise HTTPException(404, f"Run {run_id} not found")

    filename = file.filename or "upload"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    safe_name = re.sub(r"[^\w\-.]", "_", filename)[:128]

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, f"File exceeds {settings.max_upload_size_mb}MB limit")
    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    parser = LoadRunnerParser() if source == "loadrunner" else AppDynamicsParser()
    if not parser.can_parse(safe_name, content):
        raise HTTPException(422, f"The selected {source} parser does not recognize {safe_name}")

    try:
        metrics = await parser.parse(safe_name, content, run_id)
        if not metrics.transactions and not metrics.infrastructure:
            raise HTTPException(422, f"No {source} metrics could be extracted from {safe_name}")

        upload_path = f"uploads/{run_id}/{safe_name}"
        await storage.save_file(upload_path, content)
        await storage.save(f"runs/{run_id}/{source}.json", metrics.model_dump())

        meta = await storage.load(f"runs/{run_id}/metadata.json")
        meta[f"{source}_uploaded"] = True
        meta[f"{source}_upload_path"] = upload_path
        meta["status"] = "parsing"
        await storage.save(f"runs/{run_id}/metadata.json", meta)

        return {
            "status": "success",
            "run_id": run_id,
            "source": source,
            "filename": safe_name,
            "upload_path": upload_path,
            "parsed_metrics_path": f"runs/{run_id}/{source}.json",
            "transactions_parsed": len(metrics.transactions),
            "infrastructure_parsed": len(metrics.infrastructure),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parse failed for {safe_name}: {e}")
        raise HTTPException(422, f"Failed to parse file: {str(e)}")
