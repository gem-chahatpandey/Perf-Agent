from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from app.storage.filesystem import storage
from app.ai.rag import rag_engine
from app.core.security import get_current_user

router = APIRouter()


@router.post("/runs/{run_id}/documents")
async def upload_document(run_id: str, file: UploadFile = File(...), _user: str = Depends(get_current_user)):
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "Empty file")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Document exceeds 10MB limit")

    filename = file.filename or "document.txt"
    text = content.decode("utf-8", errors="ignore")

    await storage.save_file(f"runs/{run_id}/documents/{filename}", content)

    chunks_indexed = await rag_engine.index_document(
        doc_id=f"{run_id}_{filename}",
        text=text,
        metadata={"run_id": run_id, "filename": filename},
    )

    return {"status": "success", "filename": filename, "chunks_indexed": chunks_indexed}


@router.post("/runs/{run_id}/dependency-graph")
async def upload_dependency_graph(run_id: str, file: UploadFile = File(...), _user: str = Depends(get_current_user)):
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    import json
    try:
        graph_data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(422, "Invalid JSON file")

    await storage.save(f"runs/{run_id}/dependency_graph.json", graph_data)
    return {"status": "success", "run_id": run_id}
