from app.models.performance import PerformanceMetrics, SLAThresholds
from app.models.analysis import Finding, Severity, Category, AnalysisResult


class PerformanceAnalyzer:
    def __init__(self, thresholds: SLAThresholds | None = None):
        self.thresholds = thresholds or SLAThresholds()

    def analyze(self, metrics: PerformanceMetrics) -> AnalysisResult:
        findings: list[Finding] = []

        findings.extend(self._check_sla(metrics))
        findings.extend(self._check_latency(metrics))
        findings.extend(self._check_errors(metrics))
        findings.extend(self._check_throughput(metrics))
        findings.extend(self._check_infrastructure(metrics))

        sla_violations = [f for f in findings if f.category == Category.SLA]
        perf_findings = [f for f in findings if f.category in (Category.LATENCY, Category.ERROR_RATE, Category.THROUGHPUT)]
        infra_findings = [f for f in findings if f.category in (Category.CPU, Category.MEMORY, Category.JVM, Category.GC, Category.THREAD, Category.DATABASE, Category.NETWORK)]
        bottlenecks = [f for f in findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]

        top_slow = sorted(
            [{"api": t.api_name or t.transaction_name, "p95_ms": t.p95_ms, "avg_ms": t.avg_response_time_ms}
             for t in metrics.transactions if t.p95_ms > 0],
            key=lambda x: x["p95_ms"],
            reverse=True,
        )[:10]

        return AnalysisResult(
            run_id=metrics.run_id,
            total_findings=len(findings),
            critical_count=sum(1 for f in findings if f.severity == Severity.CRITICAL),
            high_count=sum(1 for f in findings if f.severity == Severity.HIGH),
            medium_count=sum(1 for f in findings if f.severity == Severity.MEDIUM),
            low_count=sum(1 for f in findings if f.severity == Severity.LOW),
            sla_violations=sla_violations,
            performance_findings=perf_findings,
            infrastructure_findings=infra_findings,
            bottlenecks=bottlenecks,
            top_slow_apis=top_slow,
        )

    def _check_sla(self, metrics: PerformanceMetrics) -> list[Finding]:
        findings = []
        for txn in metrics.transactions:
            if txn.p95_ms > self.thresholds.p95_ms:
                findings.append(Finding(
                    severity=Severity.HIGH,
                    category=Category.SLA,
                    component=txn.api_name or txn.transaction_name,
                    metric="p95_response_time_ms",
                    value=txn.p95_ms,
                    threshold=self.thresholds.p95_ms,
                    description=f"P95 response time ({txn.p95_ms:.0f}ms) exceeds SLA threshold ({self.thresholds.p95_ms:.0f}ms)",
                    api_name=txn.api_name or txn.transaction_name,
                ))
            if txn.error_rate_pct > self.thresholds.error_rate_pct:
                findings.append(Finding(
                    severity=Severity.HIGH,
                    category=Category.SLA,
                    component=txn.api_name or txn.transaction_name,
                    metric="error_rate_pct",
                    value=txn.error_rate_pct,
                    threshold=self.thresholds.error_rate_pct,
                    description=f"Error rate ({txn.error_rate_pct:.2f}%) exceeds SLA threshold ({self.thresholds.error_rate_pct:.1f}%)",
                    api_name=txn.api_name or txn.transaction_name,
                ))
        return findings

    def _check_latency(self, metrics: PerformanceMetrics) -> list[Finding]:
        findings = []
        for txn in metrics.transactions:
            if txn.p95_ms > 5000:
                findings.append(Finding(
                    severity=Severity.CRITICAL,
                    category=Category.LATENCY,
                    component=txn.api_name or txn.transaction_name,
                    metric="p95_response_time_ms",
                    value=txn.p95_ms,
                    threshold=5000,
                    description=f"Critical latency: P95 = {txn.p95_ms:.0f}ms",
                    api_name=txn.api_name or txn.transaction_name,
                ))
            elif txn.p95_ms > 3000:
                findings.append(Finding(
                    severity=Severity.HIGH,
                    category=Category.LATENCY,
                    component=txn.api_name or txn.transaction_name,
                    metric="p95_response_time_ms",
                    value=txn.p95_ms,
                    threshold=3000,
                    description=f"High latency: P95 = {txn.p95_ms:.0f}ms",
                    api_name=txn.api_name or txn.transaction_name,
                ))
        return findings

    def _check_errors(self, metrics: PerformanceMetrics) -> list[Finding]:
        findings = []
        if metrics.overall_error_rate_pct > 5:
            findings.append(Finding(
                severity=Severity.CRITICAL,
                category=Category.ERROR_RATE,
                metric="overall_error_rate_pct",
                value=metrics.overall_error_rate_pct,
                threshold=5.0,
                description=f"Critical error rate: {metrics.overall_error_rate_pct:.2f}%",
            ))
        elif metrics.overall_error_rate_pct > self.thresholds.error_rate_pct:
            findings.append(Finding(
                severity=Severity.HIGH,
                category=Category.ERROR_RATE,
                metric="overall_error_rate_pct",
                value=metrics.overall_error_rate_pct,
                threshold=self.thresholds.error_rate_pct,
                description=f"Elevated error rate: {metrics.overall_error_rate_pct:.2f}%",
            ))
        return findings

    def _check_throughput(self, metrics: PerformanceMetrics) -> list[Finding]:
        findings = []
        if metrics.avg_throughput_tps > 0 and metrics.avg_throughput_tps < self.thresholds.throughput_min_tps:
            findings.append(Finding(
                severity=Severity.MEDIUM,
                category=Category.THROUGHPUT,
                metric="avg_throughput_tps",
                value=metrics.avg_throughput_tps,
                threshold=self.thresholds.throughput_min_tps,
                description=f"Low throughput: {metrics.avg_throughput_tps:.1f} TPS",
            ))
        return findings

    def _check_infrastructure(self, metrics: PerformanceMetrics) -> list[Finding]:
        findings = []
        for infra in metrics.infrastructure:
            if infra.cpu_pct > 90:
                findings.append(Finding(
                    severity=Severity.CRITICAL, category=Category.CPU,
                    component=infra.component, metric="cpu_pct",
                    value=infra.cpu_pct, threshold=90,
                    description=f"CPU critically high: {infra.cpu_pct:.1f}% on {infra.component}",
                ))
            elif infra.cpu_pct > self.thresholds.cpu_pct:
                findings.append(Finding(
                    severity=Severity.HIGH, category=Category.CPU,
                    component=infra.component, metric="cpu_pct",
                    value=infra.cpu_pct, threshold=self.thresholds.cpu_pct,
                    description=f"CPU high: {infra.cpu_pct:.1f}% on {infra.component}",
                ))

            if infra.memory_pct > 90:
                findings.append(Finding(
                    severity=Severity.CRITICAL, category=Category.MEMORY,
                    component=infra.component, metric="memory_pct",
                    value=infra.memory_pct, threshold=90,
                    description=f"Memory critically high: {infra.memory_pct:.1f}% on {infra.component}",
                ))
            elif infra.memory_pct > self.thresholds.memory_pct:
                findings.append(Finding(
                    severity=Severity.HIGH, category=Category.MEMORY,
                    component=infra.component, metric="memory_pct",
                    value=infra.memory_pct, threshold=self.thresholds.memory_pct,
                    description=f"Memory pressure: {infra.memory_pct:.1f}% on {infra.component}",
                ))

            if infra.gc_time_ms > 500:
                findings.append(Finding(
                    severity=Severity.HIGH, category=Category.GC,
                    component=infra.component, metric="gc_time_ms",
                    value=infra.gc_time_ms, threshold=500,
                    description=f"High GC time: {infra.gc_time_ms:.0f}ms on {infra.component}",
                ))

            if infra.thread_blocked > 50:
                findings.append(Finding(
                    severity=Severity.HIGH, category=Category.THREAD,
                    component=infra.component, metric="thread_blocked",
                    value=infra.thread_blocked, threshold=50,
                    description=f"Thread contention: {infra.thread_blocked} blocked threads on {infra.component}",
                ))

            if infra.db_response_time_ms > 1000:
                findings.append(Finding(
                    severity=Severity.HIGH, category=Category.DATABASE,
                    component=infra.component, metric="db_response_time_ms",
                    value=infra.db_response_time_ms, threshold=1000,
                    description=f"Slow database: {infra.db_response_time_ms:.0f}ms on {infra.component}",
                ))

            if infra.network_latency_ms > 200:
                findings.append(Finding(
                    severity=Severity.MEDIUM, category=Category.NETWORK,
                    component=infra.component, metric="network_latency_ms",
                    value=infra.network_latency_ms, threshold=200,
                    description=f"Network latency: {infra.network_latency_ms:.0f}ms on {infra.component}",
                ))
        return findings
