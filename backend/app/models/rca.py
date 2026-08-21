from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    priority: int = 0
    category: str = ""
    action: str = ""
    rationale: str = ""
    effort: str = ""  # low | medium | high
    impact: str = ""  # low | medium | high


class RCAResult(BaseModel):
    run_id: str
    root_cause: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    severity: str = "UNKNOWN"
    contributing_factors: list[str] = []
    evidence: list[str] = []
    affected_components: list[str] = []
    related_apis: list[str] = []
    infrastructure_impact: list[str] = []
    recommendations: list[Recommendation] = []
    ai_reasoning: str = ""
    deterministic_findings_used: int = 0
    rag_context_used: bool = False
