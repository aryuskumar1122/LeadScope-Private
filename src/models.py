from typing import Annotated, Dict, List, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class TeamMember(BaseModel):
    name: str = Field(..., description="Full name of the executive or team leader")
    role: str = Field(..., description="Role/title, e.g. CEO, Co-Founder, VP Engineering")
    linkedin_url: Optional[str] = Field(
        None, description="Direct LinkedIn profile URL if discovered on-site or via search"
    )


class LLMExtractedIntelligence(BaseModel):
    """Strict schema extracted by the LLM."""
    company_overview: str = Field(
        ...,
        description="A concise, exactly 2-sentence summary of what the company does.",
    )
    target_audience: str = Field(
        ...,
        description="Who their product is built for (ICP), e.g., 'Backend engineers building real-time apps'.",
    )
    contact_points: List[str] = Field(
        default_factory=list,
        description="Generic or public contact emails (support@, sales@, contact@, etc.).",
    )
    key_leadership: List[TeamMember] = Field(
        default_factory=list,
        description="Key executive leaders, founders, or management.",
    )
    data_confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quality and completeness score of the extracted data between 0.0 and 1.0.",
    )


class AgentState(TypedDict):
    """The State dictionary managed across LangGraph nodes."""
    domain: str
    crawled_urls: List[str]
    raw_pages: Dict[str, str]  # URL -> Raw HTML
    cleaned_context: str       # Token-optimized Markdown
    intelligence: Optional[Dict]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    status: str                # 'success' | 'failed'
    error_message: Optional[str]