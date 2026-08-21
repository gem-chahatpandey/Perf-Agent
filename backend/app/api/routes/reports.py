from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from app.services.reports.service import report_service
from app.storage.filesystem import storage
from app.core.security import get_current_user

router = APIRouter()


class ReportRequest(BaseModel):
    format: str = "html"  # html | json


@router.post("/runs/{run_id}/reports")
async def generate_report(run_id: str, body: ReportRequest, _user: str = Depends(get_current_user)):
    if not await storage.exists(f"runs/{run_id}/metadata.json"):
        raise HTTPException(404, f"Run {run_id} not found")

    if body.format == "html":
        html = await report_service.generate_html(run_id)
        return {"status": "success", "format": "html", "size_bytes": len(html)}
    elif body.format == "json":
        report = await report_service.generate_json(run_id)
        return {"status": "success", "format": "json", "report": report}
    else:
        raise HTTPException(400, f"Unsupported format: {body.format}")


@router.get("/runs/{run_id}/reports")
async def list_reports(run_id: str, _user: str = Depends(get_current_user)):
    items = await storage.list(f"reports/{run_id}")
    return {"run_id": run_id, "reports": items}
