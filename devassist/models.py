from pydantic import BaseModel, Field


class AnswerResult(BaseModel):
    """Structured response from the DevAssist agent."""

    answer: str = Field(description="The main answer to the user's question")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    sources: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """A single web search result."""

    title: str
    snippet: str
    url: str


class GitHubRepo(BaseModel):
    """A GitHub repository result."""

    name: str
    full_name: str
    description: str | None
    stars: int
    url: str
    language: str | None