from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from app.services.github.analyzer import github_analyzer
from app.storage.filesystem import storage
from app.core.security import get_current_user

router = APIRouter()


class PRAnalysisRequest(BaseModel):
    repo: str
    pr_number: int


@router.post("/github/analyze-pr")
async def analyze_pr(body: PRAnalysisRequest, _user: str = Depends(get_current_user)):
    if not github_analyzer.is_configured:
        raise HTTPException(503, "GitHub token not configured")

    try:
        result = await github_analyzer.analyze_pr(body.repo, body.pr_number)
        await storage.save(f"github/pr_{body.pr_number}.json", result)
        return result
    except Exception as e:
        raise HTTPException(400, f"GitHub analysis failed: {str(e)}")
