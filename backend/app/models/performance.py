from pydantic import BaseModel, Field
from datetime import datetime


class TransactionMetric(BaseModel):
    transaction_name: str = ""
    api_name: str = ""
    method: str = ""
    url: str = ""
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p50_ms: float = 0.0
    p90_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    throughput_tps: float = 0.0
    hits_per_sec: float = 0.0
    error_rate_pct: float = 0.0
    total_requests: int = 0
    passed_transactions: int = 0
    failed_transactions: int = 0
    concurrent_users: int = 0
    sla_status: str = "unknown"
    timestamp: datetime | None = None


class InfrastructureMetric(BaseModel):
    component: str = ""
    tier: str = ""
    node: str = ""
    cpu_pct: float = 0.0
    memory_pct: float = 0.0
    memory_used_mb: float = 0.0
    jvm_heap_used_mb: float = 0.0
    jvm_heap_max_mb: float = 0.0
    gc_time_ms: float = 0.0
    gc_count: int = 0
    thread_count: int = 0
    thread_blocked: int = 0
    db_response_time_ms: float = 0.0
    db_calls_per_min: float = 0.0
    network_latency_ms: float = 0.0
    backend_latency_ms: float = 0.0
    error_rate_pct: float = 0.0
    calls_per_min: float = 0.0
    timestamp: datetime | None = None


class PerformanceMetrics(BaseModel):
    run_id: str
    source: str = ""  # "loadrunner" | "appdynamics"
    application: str = ""
    environment: str = ""
    test_start: datetime | None = None
    test_end: datetime | None = None
    duration_seconds: float = 0.0
    total_transactions: int = 0
    total_errors: int = 0
    overall_error_rate_pct: float = 0.0
    peak_concurrent_users: int = 0
    avg_throughput_tps: float = 0.0
    transactions: list[TransactionMetric] = []
    infrastructure: list[InfrastructureMetric] = []


class SLAThresholds(BaseModel):
    p95_ms: float = 3000.0
    p99_ms: float = 5000.0
    error_rate_pct: float = 1.0
    cpu_pct: float = 80.0
    memory_pct: float = 85.0
    throughput_min_tps: float = 10.0
