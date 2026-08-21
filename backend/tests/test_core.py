import pytest
import json
from app.parsers.loadrunner import LoadRunnerParser
from app.parsers.appdynamics import AppDynamicsParser
from app.services.analysis.engine import PerformanceAnalyzer
from app.models.performance import PerformanceMetrics, SLAThresholds, TransactionMetric, InfrastructureMetric


@pytest.fixture
def sample_lr_json():
    return json.dumps({
        "application": "Test App",
        "transactions": [
            {
                "transaction_name": "Login",
                "api_name": "/api/login",
                "avg_response_time": 200,
                "p95": 4000,
                "error_rate": 2.5,
                "total_requests": 1000,
                "passed": 975,
                "failed": 25,
            }
        ]
    }).encode("utf-8")


@pytest.fixture
def sample_appd_json():
    return json.dumps({
        "application": "Test App",
        "business_transactions": [
            {"name": "Checkout", "api": "/api/checkout", "avg_response_time_ms": 500, "p95_ms": 3500, "calls": 2000, "error_rate_pct": 1.5}
        ],
        "infrastructure": [
            {"component": "app-server", "tier": "Backend", "cpu_pct": 92, "memory_pct": 88, "gc_time_ms": 600, "thread_blocked": 60, "db_response_time_ms": 1200}
        ]
    }).encode("utf-8")


class TestLoadRunnerParser:
    @pytest.mark.asyncio
    async def test_can_parse_json(self, sample_lr_json):
        parser = LoadRunnerParser()
        assert parser.can_parse("report.json", sample_lr_json)

    @pytest.mark.asyncio
    async def test_parse_json(self, sample_lr_json):
        parser = LoadRunnerParser()
        result = await parser.parse("report.json", sample_lr_json, "RUN-001")
        assert result.run_id == "RUN-001"
        assert result.source == "loadrunner"
        assert len(result.transactions) == 1
        assert result.transactions[0].api_name == "/api/login"
        assert result.transactions[0].p95_ms == 4000

    @pytest.mark.asyncio
    async def test_rejects_unknown_format(self):
        parser = LoadRunnerParser()
        assert not parser.can_parse("image.png", b"binary data")

    @pytest.mark.asyncio
    async def test_parses_runtime_log(self):
        content = b'''LoadRunner Controller / VuGen Runtime Log
Scenario: Peak_Load
[14:00:00.100] Starting 1500 Vusers
[14:00:35.000] Load Generator LG01 CPU = 99%
[14:00:35.000] Load Generator LG01 memory = 96%
[14:00:42.100] Transaction response time = 3100 ms
[14:00:50.200] Vuser 832: rendezvous timeout
[14:01:00.000] LG01 CPU = 100%
[14:01:05.100] Error: insufficient resources to schedule Vuser
'''
        parser = LoadRunnerParser()

        assert parser.can_parse("runtime.log", content)
        result = await parser.parse("runtime.log", content, "RUN-LOG")

        assert result.peak_concurrent_users == 1500
        assert result.total_errors == 2
        assert result.transactions[0].p95_ms == 3100
        assert result.infrastructure[0].component == "LG01"
        assert result.infrastructure[0].cpu_pct == 99.5
        assert result.infrastructure[0].memory_pct == 96


class TestAppDynamicsParser:
    @pytest.mark.asyncio
    async def test_can_parse_json(self, sample_appd_json):
        parser = AppDynamicsParser()
        assert parser.can_parse("appd_export.json", sample_appd_json)

    @pytest.mark.asyncio
    async def test_parse_json(self, sample_appd_json):
        parser = AppDynamicsParser()
        result = await parser.parse("appd_export.json", sample_appd_json, "RUN-001")
        assert result.source == "appdynamics"
        assert len(result.transactions) == 1
        assert len(result.infrastructure) == 1
        assert result.infrastructure[0].cpu_pct == 92


class TestPerformanceAnalyzer:
    def test_detects_sla_violation(self):
        metrics = PerformanceMetrics(
            run_id="RUN-TEST",
            transactions=[
                TransactionMetric(api_name="/api/slow", p95_ms=4500, error_rate_pct=0.5)
            ]
        )
        analyzer = PerformanceAnalyzer(SLAThresholds(p95_ms=3000))
        result = analyzer.analyze(metrics)
        assert result.total_findings > 0
        assert any(f.category == "SLA" for f in result.sla_violations)

    def test_detects_cpu_bottleneck(self):
        metrics = PerformanceMetrics(
            run_id="RUN-TEST",
            infrastructure=[
                InfrastructureMetric(component="app-server", cpu_pct=95)
            ]
        )
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze(metrics)
        assert any(f.category == "CPU" for f in result.infrastructure_findings)

    def test_detects_database_issue(self):
        metrics = PerformanceMetrics(
            run_id="RUN-TEST",
            infrastructure=[
                InfrastructureMetric(component="db-server", db_response_time_ms=2000)
            ]
        )
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze(metrics)
        assert any(f.category == "DATABASE" for f in result.infrastructure_findings)

    def test_healthy_run_no_findings(self):
        metrics = PerformanceMetrics(
            run_id="RUN-OK",
            transactions=[
                TransactionMetric(api_name="/api/fast", p95_ms=200, error_rate_pct=0.1)
            ],
            infrastructure=[
                InfrastructureMetric(component="app", cpu_pct=40, memory_pct=50)
            ]
        )
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze(metrics)
        assert result.critical_count == 0
        assert result.high_count == 0
