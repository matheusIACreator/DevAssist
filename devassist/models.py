from pydantic import BaseModel, Field


class AnswerResult(BaseModel):
    """Structured response from the DevAssist agent."""

    answer: str = Field(description="The main answer to the user's question")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Sources or references used to answer",
    )
    follow_up_suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions the user might ask",
    )