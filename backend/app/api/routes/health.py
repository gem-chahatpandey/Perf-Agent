from fastapi import APIRouter
from app.ai.gemini import gemini_provider
from app.ai.rag import rag_engine
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    fs_healthy = settings.data_dir.exists()

    return {
        "status": "healthy" if fs_healthy else "degraded",
        "filesystem": "healthy" if fs_healthy else "unavailable",
        "chroma": rag_engine.get_stats()["status"],
        "gemini": "configured" if gemini_provider.is_configured() else "not_configured",
        "github": "configured" if settings.github_token else "not_configured",
    }
