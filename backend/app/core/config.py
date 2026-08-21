from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    github_token: str = ""

    poc_username: str = "admin"
    poc_password: str = "admin"
    jwt_secret: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    data_dir: Path = Path("./data")
    chroma_dir: Path = Path("./data/chroma")

    slack_webhook_url: str = ""
    teams_webhook_url: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@ai-perf-platform.local"

    max_upload_size_mb: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def runs_dir(self) -> Path:
        return self.data_dir / "runs"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def chat_dir(self) -> Path:
        return self.data_dir / "chat"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"


settings = Settings()
