import json
from app.ai.gemini import gemini_provider, GeminiNetworkBlockedError
from app.ai.prompts import RCA_PROMPT
from app.ai.rag import rag_engine
from app.models.analysis import AnalysisResult
from app.models.rca import RCAResult
from app.storage.filesystem import storage
from app.core.logging import logger


class RCAService:
    async def perform_rca(self, run_id: str, analysis: AnalysisResult) -> RCAResult:
        if not gemini_provider.is_configured():
            return RCAResult(
                run_id=run_id,
                root_cause="AI analysis unavailable - Gemini API not configured",
                confidence=0.0,
                severity="UNKNOWN",
                deterministic_findings_used=analysis.total_findings,
            )

        findings_json = json.dumps(
            [f.model_dump() for f in analysis.bottlenecks[:20]],
            indent=2,
        )

        metrics_data = {}
        try:
            metrics_data = await storage.load(f"runs/{run_id}/metrics.json")
        except FileNotFoundError:
            pass

        metrics_summary = json.dumps({
            "total_findings": analysis.total_findings,
            "critical": analysis.critical_count,
            "high": analysis.high_count,
            "top_slow_apis": analysis.top_slow_apis[:5],
        }, indent=2)

        query = f"Performance issues: {', '.join(f.description for f in analysis.bottlenecks[:5])}"
        rag_context = await rag_engine.retrieve(query, n_results=3)
        rag_text = "\n---\n".join(rag_context) if rag_context else "No relevant historical context found."

        dep_graph = "{}"
        try:
            dep_data = await storage.load(f"runs/{run_id}/dependency_graph.json")
            dep_graph = json.dumps(dep_data, indent=2)
        except FileNotFoundError:
            pass

        prompt = RCA_PROMPT.format(
            findings_json=findings_json,
            metrics_json=metrics_summary,
            rag_context=rag_text,
            dependency_graph=dep_graph,
        )

        try:
            result = await gemini_provider.generate_structured(prompt)

            rca = RCAResult(
                run_id=run_id,
                root_cause=result.get("root_cause", "Unable to determine root cause"),
                confidence=float(result.get("confidence", 0.5)),
                severity=result.get("severity", "MEDIUM"),
                contributing_factors=result.get("contributing_factors", []),
                evidence=result.get("evidence", []),
                affected_components=result.get("affected_components", []),
                related_apis=result.get("related_apis", []),
                infrastructure_impact=result.get("infrastructure_impact", []),
                recommendations=result.get("recommendations", []),
                ai_reasoning=result.get("reasoning", ""),
                deterministic_findings_used=analysis.total_findings,
                rag_context_used=bool(rag_context),
            )
            return rca
        except GeminiNetworkBlockedError as e:
            logger.error(f"RCA AI analysis blocked by network policy: {e}")
            return RCAResult(
                run_id=run_id,
                root_cause=str(e),
                confidence=0.0,
                severity=analysis.bottlenecks[0].severity.value if analysis.bottlenecks else "MEDIUM",
                evidence=[f.description for f in analysis.bottlenecks[:5]],
                deterministic_findings_used=analysis.total_findings,
            )
        except Exception as e:
            logger.error(f"RCA AI analysis failed: {e}")
            return RCAResult(
                run_id=run_id,
                root_cause=f"AI analysis failed: {type(e).__name__}. Deterministic findings available.",
                confidence=0.0,
                severity=analysis.bottlenecks[0].severity.value if analysis.bottlenecks else "MEDIUM",
                evidence=[f.description for f in analysis.bottlenecks[:5]],
                deterministic_findings_used=analysis.total_findings,
            )


rca_service = RCAService()
