from pydantic import BaseModel, Field
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Category(str, Enum):
    LATENCY = "LATENCY"
    ERROR_RATE = "ERROR_RATE"
    THROUGHPUT = "THROUGHPUT"
    CPU = "CPU"
    MEMORY = "MEMORY"
    JVM = "JVM"
    GC = "GC"
    THREAD = "THREAD"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    SLA = "SLA"
    DEPENDENCY = "DEPENDENCY"


class Finding(BaseModel):
    severity: Severity
    category: Category
    component: str = ""
    metric: str = ""
    value: float = 0.0
    threshold: float = 0.0
    description: str = ""
    api_name: str = ""
    recommendation: str = ""


class AnalysisResult(BaseModel):
    run_id: str
    status: str = "completed"
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    sla_violations: list[Finding] = []
    performance_findings: list[Finding] = []
    infrastructure_findings: list[Finding] = []
    bottlenecks: list[Finding] = []
    top_slow_apis: list[dict] = []
    summary: str = ""
