from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, auth, runs, uploads, analysis, rca, chatbot, reports, github, compare, documents, agent_test
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title="AI Performance Analysis Platform",
    version="1.0.0-poc",
    description="AI-powered performance analysis, RCA, and reporting platform (POC)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(runs.router, prefix="/api", tags=["Runs"])
app.include_router(uploads.router, prefix="/api", tags=["Uploads"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(rca.router, prefix="/api", tags=["RCA"])
app.include_router(chatbot.router, prefix="/api", tags=["Chat"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(github.router, prefix="/api", tags=["GitHub"])
app.include_router(compare.router, prefix="/api", tags=["Compare"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
if settings.app_env == "development":
    app.include_router(agent_test.router, prefix="/api", tags=["Agent Test"])


@app.on_event("startup")
async def startup():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.chat_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"AI Performance Platform started (env={settings.app_env})")
