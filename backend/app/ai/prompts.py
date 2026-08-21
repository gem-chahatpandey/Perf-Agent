PERFORMANCE_ANALYSIS_PROMPT = """You are an expert performance engineer analyzing load test results.

Based on the following deterministic findings and metrics, provide a comprehensive performance analysis.

RULES:
1. Use ONLY the supplied evidence below. Do NOT fabricate metrics.
2. Clearly distinguish between OBSERVED FACTS and INFERRED conclusions.
3. Provide confidence scores (0.0-1.0) for each inference.
4. Cite specific metric values as evidence.
5. Structure your response as valid JSON.

METRICS DATA:
{metrics_json}

DETERMINISTIC FINDINGS:
{findings_json}

Respond with JSON:
{{
  "summary": "Brief executive summary",
  "key_observations": ["observation 1", "observation 2"],
  "performance_grade": "A/B/C/D/F",
  "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
  "top_concerns": [{{"concern": "", "evidence": "", "confidence": 0.0}}],
  "recommendations": ["rec 1", "rec 2"]
}}"""

RCA_PROMPT = """You are a Root Cause Analysis expert for performance engineering.

Given the following performance data, deterministic findings, and historical context, determine the most likely root cause of the performance degradation.

RULES:
1. Only use the provided evidence. Never fabricate metrics.
2. Distinguish clearly between: observed facts, calculated findings, inferred root causes, and recommendations.
3. Provide a confidence score (0.0-1.0).
4. Explain your reasoning chain using measurable evidence.
5. If RAG context is relevant, cite it.

DETERMINISTIC FINDINGS:
{findings_json}

METRICS SUMMARY:
{metrics_json}

RAG CONTEXT (from knowledge base):
{rag_context}

DEPENDENCY GRAPH:
{dependency_graph}

Respond with JSON:
{{
  "root_cause": "Primary root cause description",
  "confidence": 0.85,
  "severity": "CRITICAL/HIGH/MEDIUM/LOW",
  "contributing_factors": ["factor 1", "factor 2"],
  "evidence": ["evidence point 1", "evidence point 2"],
  "affected_components": ["component 1"],
  "related_apis": ["api 1"],
  "infrastructure_impact": ["impact 1"],
  "recommendations": [{{"priority": 1, "action": "", "rationale": "", "effort": "low/medium/high", "impact": "low/medium/high"}}],
  "reasoning": "Step-by-step explanation of how the root cause was determined"
}}"""

CHATBOT_PROMPT = """You are an AI performance engineering assistant. You have access to performance test data, analysis results, and architecture documentation.

RULES:
1. Only reference data that exists in the provided context.
2. If you don't have enough data to answer, say so clearly.
3. Never fabricate metrics or findings.
4. Provide actionable, specific answers.
5. Reference specific Run IDs, API names, and metric values when available.

AVAILABLE CONTEXT:
{context}

CONVERSATION HISTORY:
{history}

USER QUESTION: {question}"""

EXECUTIVE_SUMMARY_PROMPT = """Generate a concise executive summary for a performance test run.

DATA:
{metrics_json}

ANALYSIS:
{analysis_json}

RCA (if available):
{rca_json}

Write a professional summary covering:
1. Overall test outcome (PASS/FAIL)
2. Key metrics (response time, throughput, error rate)
3. Critical findings
4. Business impact
5. Recommended next steps

Keep it under 500 words. Use business-friendly language."""

GITHUB_IMPACT_PROMPT = """Analyze the following GitHub PR changes and determine their potential performance impact.

PR CHANGES:
{pr_changes}

DEPENDENCY GRAPH:
{dependency_graph}

CURRENT PERFORMANCE BASELINE:
{baseline_metrics}

Respond with JSON:
{{
  "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
  "impacted_services": ["service 1"],
  "impacted_apis": ["api 1"],
  "potential_issues": ["issue 1"],
  "recommendations": ["rec 1"],
  "test_coverage_gaps": ["gap 1"]
}}"""

COMPARISON_PROMPT = """Compare the following two performance test runs and identify significant changes.

RUN 1 ({run_id_1}):
{run1_metrics}

RUN 2 ({run_id_2}):
{run2_metrics}

Respond with JSON:
{{
  "summary": "Brief comparison summary",
  "trend": "IMPROVING/DEGRADING/STABLE",
  "significant_changes": [{{"metric": "", "run1_value": 0, "run2_value": 0, "change_pct": 0, "severity": ""}}],
  "new_issues": ["issue 1"],
  "resolved_issues": ["issue 1"],
  "recommendations": ["rec 1"]
}}"""
