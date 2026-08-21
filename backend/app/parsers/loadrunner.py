import csv
import json
import io
import math
import re
from statistics import mean
from datetime import datetime
from app.parsers.base import ReportParser
from app.models.performance import PerformanceMetrics, TransactionMetric, InfrastructureMetric


class LoadRunnerParser(ReportParser):
    SUPPORTED_EXTENSIONS = {".csv", ".json", ".xml", ".txt", ".html", ".log"}

    def can_parse(self, filename: str, content: bytes) -> bool:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.SUPPORTED_EXTENSIONS:
            return False
        text = content.decode("utf-8", errors="ignore")[:2000].lower()
        lr_indicators = ["transaction", "response time", "throughput", "hits/sec", "loadrunner", "vuser", "vugen", "load generator"]
        return any(ind in text for ind in lr_indicators)

    async def parse(self, filename: str, content: bytes, run_id: str) -> PerformanceMetrics:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        text = content.decode("utf-8", errors="ignore")

        if ext == ".json":
            return self._parse_json(text, run_id)
        elif ext == ".csv":
            return self._parse_csv(text, run_id)
        elif ext == ".log":
            return self._parse_log(text, run_id)
        else:
            return self._parse_text(text, run_id)

    def _parse_json(self, text: str, run_id: str) -> PerformanceMetrics:
        data = json.loads(text)

        transactions = []
        raw_transactions = data if isinstance(data, list) else data.get("transactions", data.get("results", []))

        for item in raw_transactions:
            if not isinstance(item, dict):
                continue
            txn = TransactionMetric(
                transaction_name=item.get("transaction_name", item.get("name", "")),
                api_name=item.get("api_name", item.get("api", item.get("url", ""))),
                method=item.get("method", ""),
                avg_response_time_ms=float(item.get("avg_response_time", item.get("avg_rt", 0))),
                min_response_time_ms=float(item.get("min_response_time", item.get("min_rt", 0))),
                max_response_time_ms=float(item.get("max_response_time", item.get("max_rt", 0))),
                p50_ms=float(item.get("p50", item.get("median", 0))),
                p90_ms=float(item.get("p90", item.get("percentile_90", 0))),
                p95_ms=float(item.get("p95", item.get("percentile_95", 0))),
                p99_ms=float(item.get("p99", item.get("percentile_99", 0))),
                throughput_tps=float(item.get("throughput", item.get("tps", 0))),
                hits_per_sec=float(item.get("hits_per_sec", item.get("hits", 0))),
                error_rate_pct=float(item.get("error_rate", item.get("error_pct", 0))),
                total_requests=int(item.get("total_requests", item.get("count", 0))),
                passed_transactions=int(item.get("passed", item.get("success", 0))),
                failed_transactions=int(item.get("failed", item.get("errors", 0))),
                concurrent_users=int(item.get("concurrent_users", item.get("vusers", 0))),
                sla_status=item.get("sla_status", "unknown"),
            )
            transactions.append(txn)

        meta = data if isinstance(data, dict) else {}
        total_errors = sum(t.failed_transactions for t in transactions)
        total_txns = sum(t.total_requests for t in transactions)

        return PerformanceMetrics(
            run_id=run_id,
            source="loadrunner",
            application=meta.get("application", ""),
            environment=meta.get("environment", ""),
            duration_seconds=float(meta.get("duration_seconds", 0)),
            total_transactions=total_txns,
            total_errors=total_errors,
            overall_error_rate_pct=(total_errors / total_txns * 100) if total_txns > 0 else 0,
            peak_concurrent_users=int(meta.get("peak_users", max((t.concurrent_users for t in transactions), default=0))),
            avg_throughput_tps=float(meta.get("avg_throughput", 0)),
            transactions=transactions,
        )

    def _parse_csv(self, text: str, run_id: str) -> PerformanceMetrics:
        reader = csv.DictReader(io.StringIO(text))
        transactions = []

        for row in reader:
            txn = TransactionMetric(
                transaction_name=row.get("Transaction Name", row.get("transaction_name", row.get("Name", ""))),
                api_name=row.get("API", row.get("api_name", row.get("URL", ""))),
                method=row.get("Method", ""),
                avg_response_time_ms=float(row.get("Avg Response Time", row.get("avg_response_time", 0)) or 0),
                min_response_time_ms=float(row.get("Min Response Time", row.get("min_response_time", 0)) or 0),
                max_response_time_ms=float(row.get("Max Response Time", row.get("max_response_time", 0)) or 0),
                p90_ms=float(row.get("90th Percentile", row.get("p90", 0)) or 0),
                p95_ms=float(row.get("95th Percentile", row.get("p95", 0)) or 0),
                throughput_tps=float(row.get("Throughput", row.get("throughput", 0)) or 0),
                error_rate_pct=float(row.get("Error Rate", row.get("error_rate", 0)) or 0),
                total_requests=int(float(row.get("Total Requests", row.get("total", 0)) or 0)),
                passed_transactions=int(float(row.get("Passed", row.get("passed", 0)) or 0)),
                failed_transactions=int(float(row.get("Failed", row.get("failed", 0)) or 0)),
                sla_status=row.get("SLA Status", row.get("sla", "unknown")),
            )
            transactions.append(txn)

        total_errors = sum(t.failed_transactions for t in transactions)
        total_txns = sum(t.total_requests for t in transactions)

        return PerformanceMetrics(
            run_id=run_id,
            source="loadrunner",
            total_transactions=total_txns,
            total_errors=total_errors,
            overall_error_rate_pct=(total_errors / total_txns * 100) if total_txns > 0 else 0,
            peak_concurrent_users=max((t.concurrent_users for t in transactions), default=0),
            transactions=transactions,
        )

    def _parse_text(self, text: str, run_id: str) -> PerformanceMetrics:
        return PerformanceMetrics(run_id=run_id, source="loadrunner")

    _SCENARIO_PATTERN = re.compile(r"^Scenario:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    _VUSER_PATTERN = re.compile(r"\b(\d+)\s+Vusers?\b", re.IGNORECASE)
    _CPU_PATTERN = re.compile(r"(?:Load Generator\s+)?([\w.-]+)\s+CPU\s*=\s*([\d.]+)%", re.IGNORECASE)
    _MEMORY_PATTERN = re.compile(r"(?:Load Generator\s+)?([\w.-]+)\s+memory\s*=\s*([\d.]+)%", re.IGNORECASE)
    _RESPONSE_TIME_PATTERN = re.compile(r"Transaction response time\s*=\s*([\d.]+)\s*ms", re.IGNORECASE)
    _FAILURE_PATTERN = re.compile(r"(?:error:|timeout|\bdelayed\b|insufficient resources)", re.IGNORECASE)

    def _parse_log(self, text: str, run_id: str) -> PerformanceMetrics:
        scenario_match = self._SCENARIO_PATTERN.search(text)
        scenario = scenario_match.group(1).strip() if scenario_match else "LoadRunner runtime"
        response_times = [float(value) for value in self._RESPONSE_TIME_PATTERN.findall(text)]
        failures = sum(1 for line in text.splitlines() if self._FAILURE_PATTERN.search(line))
        total_requests = max(len(response_times), failures)

        component_samples: dict[str, dict[str, list[float]]] = {}
        for component, value in self._CPU_PATTERN.findall(text):
            component_samples.setdefault(component, {"cpu": [], "memory": []})["cpu"].append(float(value))
        for component, value in self._MEMORY_PATTERN.findall(text):
            component_samples.setdefault(component, {"cpu": [], "memory": []})["memory"].append(float(value))

        transactions = []
        if response_times or failures:
            sorted_times = sorted(response_times)
            p95_index = max(0, math.ceil(len(sorted_times) * 0.95) - 1)
            transactions.append(TransactionMetric(
                transaction_name=scenario,
                api_name=scenario,
                avg_response_time_ms=mean(response_times) if response_times else 0.0,
                min_response_time_ms=min(response_times) if response_times else 0.0,
                max_response_time_ms=max(response_times) if response_times else 0.0,
                p95_ms=sorted_times[p95_index] if sorted_times else 0.0,
                error_rate_pct=(failures / total_requests * 100) if total_requests else 0.0,
                total_requests=total_requests,
                passed_transactions=max(0, total_requests - failures),
                failed_transactions=failures,
            ))

        infrastructure = [
            InfrastructureMetric(
                component=component,
                cpu_pct=mean(samples["cpu"]) if samples["cpu"] else 0.0,
                memory_pct=mean(samples["memory"]) if samples["memory"] else 0.0,
            )
            for component, samples in component_samples.items()
        ]

        return PerformanceMetrics(
            run_id=run_id,
            source="loadrunner",
            peak_concurrent_users=max((int(value) for value in self._VUSER_PATTERN.findall(text)), default=0),
            total_transactions=total_requests,
            total_errors=failures,
            overall_error_rate_pct=(failures / total_requests * 100) if total_requests else 0.0,
            transactions=transactions,
            infrastructure=infrastructure,
        )
