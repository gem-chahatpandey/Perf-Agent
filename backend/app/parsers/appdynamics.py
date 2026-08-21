import csv
import json
import io
import re
import math
from statistics import mean
from app.parsers.base import ReportParser
from app.models.performance import PerformanceMetrics, TransactionMetric, InfrastructureMetric


class AppDynamicsParser(ReportParser):
    SUPPORTED_EXTENSIONS = {".csv", ".json", ".xml", ".txt" , ".log"}

    def can_parse(self, filename: str, content: bytes) -> bool:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.SUPPORTED_EXTENSIONS:
            return False
        text = content.decode("utf-8", errors="ignore")[:2000].lower()
        appd_indicators = ["appdynamics", "tier", "node", "business transaction", "bt ", "backend"]
        if ext == ".log":
            appd_indicators += ["app=", "node=", "transaction=", "response_time_ms", "cpu_pct"]
        return any(ind in text for ind in appd_indicators)

    async def parse(self, filename: str, content: bytes, run_id: str) -> PerformanceMetrics:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        text = content.decode("utf-8", errors="ignore")

        if ext == ".json":
            return self._parse_json(text, run_id)
        elif ext == ".csv":
            return self._parse_csv(text, run_id)
        elif ext == ".log":
            return self._parse_log(text, run_id)
        return PerformanceMetrics(run_id=run_id, source="appdynamics")

    def _parse_json(self, text: str, run_id: str) -> PerformanceMetrics:
        data = json.loads(text)
        meta = data if isinstance(data, dict) else {}

        transactions = []
        infra_metrics = []

        raw_bts = meta.get("business_transactions", meta.get("transactions", []))
        for bt in raw_bts:
            if not isinstance(bt, dict):
                continue
            txn = TransactionMetric(
                transaction_name=bt.get("name", bt.get("bt_name", "")),
                api_name=bt.get("api", bt.get("entry_point", "")),
                avg_response_time_ms=float(bt.get("avg_response_time_ms", bt.get("avg_rt", 0))),
                p95_ms=float(bt.get("p95_ms", bt.get("p95", 0))),
                p99_ms=float(bt.get("p99_ms", bt.get("p99", 0))),
                error_rate_pct=float(bt.get("error_rate_pct", bt.get("errors_pct", 0))),
                total_requests=int(bt.get("calls", bt.get("total_calls", 0))),
                throughput_tps=float(bt.get("calls_per_min", 0)) / 60.0,
            )
            transactions.append(txn)

        raw_infra = meta.get("infrastructure", meta.get("nodes", meta.get("tiers", [])))
        for node in raw_infra:
            if not isinstance(node, dict):
                continue
            infra = InfrastructureMetric(
                component=node.get("component", node.get("name", "")),
                tier=node.get("tier", ""),
                node=node.get("node", ""),
                cpu_pct=float(node.get("cpu_pct", node.get("cpu", 0))),
                memory_pct=float(node.get("memory_pct", node.get("memory", 0))),
                memory_used_mb=float(node.get("memory_used_mb", 0)),
                jvm_heap_used_mb=float(node.get("jvm_heap_used_mb", node.get("heap_used", 0))),
                jvm_heap_max_mb=float(node.get("jvm_heap_max_mb", node.get("heap_max", 0))),
                gc_time_ms=float(node.get("gc_time_ms", node.get("gc_time", 0))),
                gc_count=int(node.get("gc_count", 0)),
                thread_count=int(node.get("thread_count", node.get("threads", 0))),
                thread_blocked=int(node.get("thread_blocked", node.get("blocked_threads", 0))),
                db_response_time_ms=float(node.get("db_response_time_ms", node.get("db_rt", 0))),
                db_calls_per_min=float(node.get("db_calls_per_min", 0)),
                network_latency_ms=float(node.get("network_latency_ms", 0)),
                backend_latency_ms=float(node.get("backend_latency_ms", 0)),
                error_rate_pct=float(node.get("error_rate_pct", 0)),
                calls_per_min=float(node.get("calls_per_min", 0)),
            )
            infra_metrics.append(infra)

        return PerformanceMetrics(
            run_id=run_id,
            source="appdynamics",
            application=meta.get("application", ""),
            environment=meta.get("environment", ""),
            duration_seconds=float(meta.get("duration_seconds", 0)),
            total_transactions=sum(t.total_requests for t in transactions),
            total_errors=sum(int(t.total_requests * t.error_rate_pct / 100) for t in transactions),
            overall_error_rate_pct=float(meta.get("overall_error_rate_pct", 0)),
            peak_concurrent_users=int(meta.get("peak_concurrent_users", 0)),
            transactions=transactions,
            infrastructure=infra_metrics,
        )

    def _parse_csv(self, text: str, run_id: str) -> PerformanceMetrics:
        reader = csv.DictReader(io.StringIO(text))
        infra_metrics = []
        transactions = []

        for row in reader:
            if row.get("Tier") or row.get("tier") or row.get("Node") or row.get("node"):
                infra = InfrastructureMetric(
                    component=row.get("Component", row.get("component", "")),
                    tier=row.get("Tier", row.get("tier", "")),
                    node=row.get("Node", row.get("node", "")),
                    cpu_pct=float(row.get("CPU %", row.get("cpu_pct", 0)) or 0),
                    memory_pct=float(row.get("Memory %", row.get("memory_pct", 0)) or 0),
                    jvm_heap_used_mb=float(row.get("Heap Used MB", row.get("heap_used_mb", 0)) or 0),
                    gc_time_ms=float(row.get("GC Time ms", row.get("gc_time_ms", 0)) or 0),
                    thread_count=int(float(row.get("Threads", row.get("thread_count", 0)) or 0)),
                    db_response_time_ms=float(row.get("DB RT ms", row.get("db_rt_ms", 0)) or 0),
                )
                infra_metrics.append(infra)
            else:
                txn = TransactionMetric(
                    transaction_name=row.get("Business Transaction", row.get("bt_name", "")),
                    avg_response_time_ms=float(row.get("Avg RT", row.get("avg_rt", 0)) or 0),
                    error_rate_pct=float(row.get("Error %", row.get("error_pct", 0)) or 0),
                    total_requests=int(float(row.get("Calls", row.get("calls", 0)) or 0)),
                )
                transactions.append(txn)

        return PerformanceMetrics(
            run_id=run_id,
            source="appdynamics",
            transactions=transactions,
            infrastructure=infra_metrics,
        )

    _KV_PATTERN = re.compile(r'(\w+)=("[^"]*"|\S+)')
    _LOG_LEVEL_PATTERN = re.compile(r"\|\s*(INFO|WARN|ERROR|DEBUG)\s*\|")
    _NARRATIVE_TIMESTAMP_PATTERN = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]")

    def _parse_log(self, text: str, run_id: str) -> PerformanceMetrics:
        # narrative-style logs use bracketed timestamps and prose metric lines, not key=value pairs
        sample_lines = [l.strip() for l in text.splitlines() if l.strip()][:20]
        if any(self._NARRATIVE_TIMESTAMP_PATTERN.match(l) for l in sample_lines):
            return self._parse_narrative_log(text, run_id)

        samples = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # each log line is either a JSON object or a pipe-delimited key=value record
            if line.startswith("{"):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
            else:
                row = {k: v.strip('"') for k, v in self._KV_PATTERN.findall(line)}
                level_match = self._LOG_LEVEL_PATTERN.search(line)
                if level_match:
                    row["level"] = level_match.group(1)

            if row:
                samples.append(row)

        if not samples:
            return PerformanceMetrics(run_id=run_id, source="appdynamics")

        # group samples by transaction name and by service/node for aggregation
        txn_groups: dict[str, list[dict]] = {}
        infra_groups: dict[tuple[str, str], list[dict]] = {}

        for row in samples:
            txn_name = row.get("transaction", row.get("bt_name", ""))
            if txn_name:
                txn_groups.setdefault(txn_name, []).append(row)

            component = row.get("app", row.get("component", ""))
            node = row.get("node", "")
            if component or node:
                infra_groups.setdefault((component, node), []).append(row)

        transactions = []
        for name, rows in txn_groups.items():
            response_times = sorted(
                float(r["response_time_ms"]) for r in rows if "response_time_ms" in r
            )
            total_requests = sum(int(float(r.get("requests", r.get("calls", 0)))) for r in rows)
            error_count = sum(1 for r in rows if str(r.get("status", "200"))[:1] in ("4", "5"))
            p95_index = max(0, math.ceil(len(response_times) * 0.95) - 1)

            transactions.append(TransactionMetric(
                transaction_name=name,
                api_name=name,
                avg_response_time_ms=mean(response_times) if response_times else 0.0,
                min_response_time_ms=min(response_times) if response_times else 0.0,
                max_response_time_ms=max(response_times) if response_times else 0.0,
                p95_ms=response_times[p95_index] if response_times else 0.0,
                error_rate_pct=(error_count / len(rows) * 100) if rows else 0.0,
                total_requests=total_requests,
                passed_transactions=total_requests - error_count,
                failed_transactions=error_count,
            ))

        infra_metrics = []
        for (component, node), rows in infra_groups.items():
            cpu_values = [float(r["cpu_pct"]) for r in rows if "cpu_pct" in r]
            mem_values = [float(r["memory_pct"]) for r in rows if "memory_pct" in r]
            error_count = sum(
                1 for r in rows
                if r.get("level") == "ERROR" or str(r.get("status", "200"))[:1] == "5"
            )

            infra_metrics.append(InfrastructureMetric(
                component=component,
                node=node,
                cpu_pct=mean(cpu_values) if cpu_values else 0.0,
                memory_pct=mean(mem_values) if mem_values else 0.0,
                error_rate_pct=(error_count / len(rows) * 100) if rows else 0.0,
                calls_per_min=float(len(rows)),
            ))

        total_txns = sum(t.total_requests for t in transactions)
        total_errors = sum(t.failed_transactions for t in transactions)

        return PerformanceMetrics(
            run_id=run_id,
            source="appdynamics",
            total_transactions=total_txns,
            total_errors=total_errors,
            overall_error_rate_pct=(total_errors / total_txns * 100) if total_txns > 0 else 0.0,
            transactions=transactions,
            infrastructure=infra_metrics,
        )

    _NARRATIVE_APPLICATION_PATTERN = re.compile(r"^Application:\s*(.+)$")
    _NARRATIVE_LOAD_PATTERN = re.compile(r"Load:\s*(\d+)\s*Vusers")
    _NARRATIVE_THROUGHPUT_PATTERN = re.compile(r"Throughput(?:\s*dropped(?:\s*to)?)?:?\s*(\d+)\s*req/min")
    _NARRATIVE_AVG_RESPONSE_PATTERN = re.compile(r"^(.*?)\s+Avg(?:\s*Response)?:\s*(\d+(?:\.\d+)?)\s*ms")
    _NARRATIVE_ERROR_RATE_PATTERN = re.compile(r"^(.*?)Error Rate:\s*([\d.]+)%")
    _NARRATIVE_CPU_PATTERN = re.compile(r"^(?:([\w]+)\s+)?CPU:\s*(\d+(?:\.\d+)?)%")
    _NARRATIVE_JVM_HEAP_PATTERN = re.compile(r"JVM Heap(?:\s*Used)?:\s*(\d+(?:\.\d+)?)%")
    _NARRATIVE_GC_PAUSE_PATTERN = re.compile(r"GC Pause:\s*(\d+(?:\.\d+)?)\s*ms")
    _NARRATIVE_JDBC_CALL_PATTERN = re.compile(r"JDBC Call:.*\|\s*(\d+(?:\.\d+)?)\s*ms")
    _NARRATIVE_CONN_WAIT_PATTERN = re.compile(r"Connection Wait Time:\s*(\d+(?:\.\d+)?)\s*ms")
    _NARRATIVE_CONN_QUEUE_PATTERN = re.compile(r"(?:Connection Wait Queue|Thread Queue):\s*(\d+)")
    _NARRATIVE_POOL_PATTERN = re.compile(r"(?:JDBC Pool Active|Web Thread Pool):\s*(\d+)\s*/\s*(\d+)")
    _NARRATIVE_DB_SESSIONS_PATTERN = re.compile(r"DB Active Sessions:\s*(\d+)")

    def _parse_narrative_log(self, text: str, run_id: str) -> PerformanceMetrics:
        application = ""
        peak_concurrent_users = 0
        throughput_samples: list[float] = []
        overall_error_samples: list[float] = []
        txn_response_times: dict[str, list[float]] = {}
        txn_error_rates: dict[str, list[float]] = {}
        infra_cpu: dict[str, list[float]] = {}
        infra_memory: dict[str, list[float]] = {}
        infra_gc: dict[str, list[float]] = {}
        infra_db_rt: dict[str, list[float]] = {}
        infra_thread_count: dict[str, list[float]] = {}
        infra_thread_blocked: dict[str, list[float]] = {}

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            app_match = self._NARRATIVE_APPLICATION_PATTERN.match(line)
            if app_match:
                application = app_match.group(1).strip()
                continue

            content = re.sub(r"^\[\d{2}:\d{2}:\d{2}\]\s*", "", line)

            load_match = self._NARRATIVE_LOAD_PATTERN.search(content)
            if load_match:
                peak_concurrent_users = max(peak_concurrent_users, int(load_match.group(1)))
                continue

            throughput_match = self._NARRATIVE_THROUGHPUT_PATTERN.search(content)
            if throughput_match:
                throughput_samples.append(float(throughput_match.group(1)))
                continue

            error_rate_match = self._NARRATIVE_ERROR_RATE_PATTERN.search(content)
            if error_rate_match:
                prefix = re.sub(r"^Business Transaction:\s*", "", error_rate_match.group(1)).strip()
                value = float(error_rate_match.group(2))
                if prefix:
                    txn_error_rates.setdefault(prefix, []).append(value)
                else:
                    overall_error_samples.append(value)
                continue

            avg_response_match = self._NARRATIVE_AVG_RESPONSE_PATTERN.search(content)
            if avg_response_match:
                name = avg_response_match.group(1).strip().rstrip("|").strip()
                name = re.sub(r"^Business Transaction:\s*", "", name)
                if name:
                    txn_response_times.setdefault(name, []).append(float(avg_response_match.group(2)))
                continue

            cpu_match = self._NARRATIVE_CPU_PATTERN.search(content)
            if cpu_match:
                component = cpu_match.group(1) or "app-server"
                infra_cpu.setdefault(component, []).append(float(cpu_match.group(2)))
                continue

            jvm_match = self._NARRATIVE_JVM_HEAP_PATTERN.search(content)
            if jvm_match:
                infra_memory.setdefault("jvm", []).append(float(jvm_match.group(1)))
                continue

            gc_match = self._NARRATIVE_GC_PAUSE_PATTERN.search(content)
            if gc_match:
                infra_gc.setdefault("jvm", []).append(float(gc_match.group(1)))
                continue

            jdbc_match = self._NARRATIVE_JDBC_CALL_PATTERN.search(content)
            if jdbc_match:
                infra_db_rt.setdefault("database", []).append(float(jdbc_match.group(1)))
                continue

            conn_wait_match = self._NARRATIVE_CONN_WAIT_PATTERN.search(content)
            if conn_wait_match:
                infra_db_rt.setdefault("connection-pool", []).append(float(conn_wait_match.group(1)))
                continue

            conn_queue_match = self._NARRATIVE_CONN_QUEUE_PATTERN.search(content)
            if conn_queue_match:
                infra_thread_blocked.setdefault("app-server", []).append(float(conn_queue_match.group(1)))
                continue

            pool_match = self._NARRATIVE_POOL_PATTERN.search(content)
            if pool_match:
                infra_thread_count.setdefault("app-server", []).append(float(pool_match.group(1)))
                continue

            db_sessions_match = self._NARRATIVE_DB_SESSIONS_PATTERN.search(content)
            if db_sessions_match:
                infra_thread_count.setdefault("database", []).append(float(db_sessions_match.group(1)))
                continue

        transactions = []
        for name, samples in txn_response_times.items():
            sorted_samples = sorted(samples)
            p95_index = max(0, math.ceil(len(sorted_samples) * 0.95) - 1)
            error_rates = txn_error_rates.get(name, [])
            transactions.append(TransactionMetric(
                transaction_name=name,
                api_name=name,
                avg_response_time_ms=mean(sorted_samples),
                min_response_time_ms=min(sorted_samples),
                max_response_time_ms=max(sorted_samples),
                p95_ms=sorted_samples[p95_index],
                error_rate_pct=mean(error_rates) if error_rates else 0.0,
            ))
        # error-rate-only lines with no matching response-time samples (e.g. "Customer_Verify Error Rate: 7.2%")
        for name, error_rates in txn_error_rates.items():
            if name not in txn_response_times:
                transactions.append(TransactionMetric(
                    transaction_name=name,
                    api_name=name,
                    error_rate_pct=mean(error_rates),
                ))

        components = set(infra_cpu) | set(infra_memory) | set(infra_gc) | set(infra_db_rt) | set(infra_thread_count) | set(infra_thread_blocked)
        infra_metrics = []
        for component in components:
            infra_metrics.append(InfrastructureMetric(
                component=component,
                cpu_pct=mean(infra_cpu[component]) if component in infra_cpu else 0.0,
                memory_pct=mean(infra_memory[component]) if component in infra_memory else 0.0,
                gc_time_ms=mean(infra_gc[component]) if component in infra_gc else 0.0,
                db_response_time_ms=mean(infra_db_rt[component]) if component in infra_db_rt else 0.0,
                thread_count=int(mean(infra_thread_count[component])) if component in infra_thread_count else 0,
                thread_blocked=int(mean(infra_thread_blocked[component])) if component in infra_thread_blocked else 0,
            ))

        return PerformanceMetrics(
            run_id=run_id,
            source="appdynamics",
            application=application,
            overall_error_rate_pct=mean(overall_error_samples) if overall_error_samples else 0.0,
            peak_concurrent_users=peak_concurrent_users,
            avg_throughput_tps=(mean(throughput_samples) / 60.0) if throughput_samples else 0.0,
            transactions=transactions,
            infrastructure=infra_metrics,
        )
