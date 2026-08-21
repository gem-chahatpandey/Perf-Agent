import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from jinja2 import Template
from app.storage.filesystem import storage
from app.core.config import settings
from app.core.logging import logger

REPORT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Performance Report - {{ run_id }}</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f8fafc; }
h1 { color: #0f172a; } h2 { color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }
.card { background: #fff; border-radius: 12px; padding: 20px; margin: 16px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.metric { display: inline-block; margin: 8px 16px 8px 0; }
.metric-value { font-size: 1.8rem; font-weight: 700; color: #1d4ed8; }
.metric-label { font-size: 0.85rem; color: #64748b; }
.severity-CRITICAL { color: #dc2626; } .severity-HIGH { color: #ea580c; }
.severity-MEDIUM { color: #d97706; } .severity-LOW { color: #65a30d; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
th { background: #f1f5f9; font-size: 0.85rem; color: #475569; text-transform: uppercase; }
.badge { padding: 4px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 700; }
.badge-pass { background: #dcfce7; color: #166534; }
.badge-fail { background: #fee2e2; color: #991b1b; }
</style>
</head>
<body>
<h1>Performance Test Report</h1>
<p><strong>Run ID:</strong> {{ run_id }} | <strong>Generated:</strong> {{ generated_at }}</p>

<div class="card">
<h2>Executive Summary</h2>
<p>{{ summary }}</p>
<div>
<span class="metric"><span class="metric-value">{{ total_transactions }}</span><span class="metric-label"> Total Transactions</span></span>
<span class="metric"><span class="metric-value">{{ error_rate }}%</span><span class="metric-label"> Error Rate</span></span>
<span class="metric"><span class="metric-value">{{ findings_count }}</span><span class="metric-label"> Findings</span></span>
</div>
</div>

{% if top_slow_apis %}
<div class="card">
<h2>Top Slow APIs</h2>
<table>
<tr><th>API</th><th>P95 (ms)</th><th>Avg (ms)</th></tr>
{% for api in top_slow_apis %}
<tr><td>{{ api.api }}</td><td>{{ "%.0f"|format(api.p95_ms) }}</td><td>{{ "%.0f"|format(api.avg_ms) }}</td></tr>
{% endfor %}
</table>
</div>
{% endif %}

{% if bottlenecks %}
<div class="card">
<h2>Bottlenecks</h2>
<table>
<tr><th>Severity</th><th>Category</th><th>Component</th><th>Description</th></tr>
{% for b in bottlenecks %}
<tr><td class="severity-{{ b.severity }}">{{ b.severity }}</td><td>{{ b.category }}</td><td>{{ b.component }}</td><td>{{ b.description }}</td></tr>
{% endfor %}
</table>
</div>
{% endif %}

{% if rca %}
<div class="card">
<h2>Root Cause Analysis</h2>
<p><strong>Root Cause:</strong> {{ rca.root_cause }}</p>
<p><strong>Confidence:</strong> {{ "%.0f"|format(rca.confidence * 100) }}% | <strong>Severity:</strong> {{ rca.severity }}</p>
{% if rca.recommendations %}
<h3>Recommendations</h3>
<ul>{% for r in rca.recommendations %}<li>{{ r.action }} <span style="color:#94a3b8">(effort: {{ r.effort or "—" }}, impact: {{ r.impact or "—" }})</span></li>{% endfor %}</ul>
{% endif %}
</div>
{% endif %}

</body></html>"""


class ReportService:
    async def generate_html(self, run_id: str) -> str:
        analysis = await self._load_analysis(run_id)
        rca = await self._load_rca(run_id)

        template = Template(REPORT_HTML_TEMPLATE)
        html = template.render(
            run_id=run_id,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary=analysis.get("summary", "Analysis completed"),
            total_transactions=analysis.get("total_findings", 0),
            error_rate=f"{analysis.get('overall_error_rate', 0):.2f}",
            findings_count=analysis.get("total_findings", 0),
            top_slow_apis=analysis.get("top_slow_apis", []),
            bottlenecks=analysis.get("bottlenecks", [])[:10],
            rca=rca,
        )

        await storage.save_file(f"reports/{run_id}/report.html", html.encode("utf-8"))
        return html

    async def generate_json(self, run_id: str) -> dict:
        analysis = await self._load_analysis(run_id)
        rca = await self._load_rca(run_id)

        report = {
            "run_id": run_id,
            "generated_at": datetime.now().isoformat(),
            "analysis": analysis,
            "rca": rca,
        }
        await storage.save(f"reports/{run_id}/report.json", report)
        return report

    async def _load_analysis(self, run_id: str) -> dict:
        try:
            return await storage.load(f"runs/{run_id}/analysis.json")
        except FileNotFoundError:
            return {}

    async def _load_rca(self, run_id: str) -> dict:
        try:
            return await storage.load(f"runs/{run_id}/rca.json")
        except FileNotFoundError:
            return {}


report_service = ReportService()
