from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class RunStatus(str, Enum):
    CREATED = "created"
    UPLOADING = "uploading"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class RunCreate(BaseModel):
    run_id: str = Field(..., pattern=r"^[A-Za-z0-9_\-]+$", max_length=64)
    name: str = Field("", max_length=256)
    description: str = ""


class RunMetadata(BaseModel):
    run_id: str
    name: str = ""
    description: str = ""
    status: RunStatus = RunStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    loadrunner_uploaded: bool = False
    loadrunner_upload_path: str = ""
    appdynamics_uploaded: bool = False
    appdynamics_upload_path: str = ""
    analysis_completed: bool = False
    rca_completed: bool = False
    report_generated: bool = False
    tags: list[str] = []
