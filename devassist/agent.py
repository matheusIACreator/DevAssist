from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from devassist.models import AnswerResult, GitHubRepo, SearchResult
from devassist.tools import calculate, get_current_datetime, get_python_info, read_local_file

load_dotenv()


# --- Deps agora incluem o httpx.AsyncClient ---
@dataclass
class AgentDeps:
    user_name: str
    session_id: str
    http_client: httpx.AsyncClient  # NOVO


# --- Agent ---
agent = Agent(
    model="openai:gpt-4o-mini",
    deps_type=AgentDeps,
    output_type=AnswerResult,
    instructions=(
        "You are DevAssist, an AI agent for developer productivity. "
        "Answer technical questions clearly and concisely. "
        "Use your tools to fetch real data when the question requires it. "
        "Always provide a confidence score honestly."
    ),
)


# --- Tools síncronas (sem I/O) ---
@agent.tool
def get_user_context(ctx: RunContext[AgentDeps]) -> str:
    """Get the current user's name and session information."""
    return f"User: {ctx.deps.user_name} | Session: {ctx.deps.session_id}"


@agent.tool_plain
def current_datetime() -> str:
    """Get the current date and time."""
    return get_current_datetime()


@agent.tool_plain
def python_environment() -> dict[str, str]:
    """Get information about the Python environment."""
    return get_python_info()


@agent.tool_plain
def math_calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Args: expression: e.g. '2 + 2'"""
    return calculate(expression)


@agent.tool_plain
def read_file(file_path: str) -> str:
    """
    Read the contents of a local file and return its text.
    
    Args:
        file_path: Path to the file, e.g. './README.md' or '~/notes.txt'
    """
    return read_local_file(file_path)


# --- Tools async (com I/O real via httpx) ---
@agent.tool
async def web_search(ctx: RunContext[AgentDeps], query: str) -> list[SearchResult]:
    """
    Search the web using DuckDuckGo and return top results.
    
    Args:
        query: The search query string.
    """
    params = {
        "q": query,
        "format": "json",
        "no_redirect": "1",
        "no_html": "1",
    }
    try:
        response = await ctx.deps.http_client.get(
            "https://api.duckduckgo.com/",
            params=params,
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        # RelatedTopics tem os resultados principais
        for item in data.get("RelatedTopics", [])[:5]:
            if "Text" in item and "FirstURL" in item:
                results.append(
                    SearchResult(
                        title=item.get("Text", "")[:80],
                        snippet=item.get("Text", ""),
                        url=item.get("FirstURL", ""),
                    )
                )
        if not results:
            return [SearchResult(title="No results", snippet="No results found.", url="")]
        return results
    except Exception as e:
        return [SearchResult(title="Error", snippet=str(e), url="")]


@agent.tool
async def github_search(
    ctx: RunContext[AgentDeps], query: str, max_results: int = 5
) -> list[GitHubRepo]:
    """
    Search GitHub repositories.
    
    Args:
        query: Search terms, e.g. 'pydantic-ai agent'
        max_results: Number of repos to return (default 5, max 10)
    """
    max_results = min(max_results, 10)
    try:
        response = await ctx.deps.http_client.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "per_page": max_results},
            headers={"Accept": "application/vnd.github+json"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        return [
            GitHubRepo(
                name=repo["name"],
                full_name=repo["full_name"],
                description=repo.get("description"),
                stars=repo["stargazers_count"],
                url=repo["html_url"],
                language=repo.get("language"),
            )
            for repo in data.get("items", [])
        ]
    except Exception as e:
        return []


# --- Runner ---
async def ask(question: str, user_name: str = "Developer") -> AnswerResult:
    """Run the agent with a question."""
    async with httpx.AsyncClient() as client:
        deps = AgentDeps(
            user_name=user_name,
            session_id="session-001",
            http_client=client,
        )
        result = await agent.run(question, deps=deps)
    return result.output


async def main() -> None:
    questions = [
        "Search GitHub for the top repos about pydantic-ai and summarize what you find.",
        "What is 999 * 37?",
        "Read the file ./README.md and tell me what this project is about.",
    ]

    for q in questions:
        print("=" * 60)
        print(f"Q: {q}")
        result = await ask(q)
        print(f"A: {result.answer}")
        print(f"Confidence: {result.confidence * 100:.0f}%")
        if result.sources:
            print(f"Sources: {', '.join(result.sources)}")
        if result.follow_up_suggestions:
            print(f"Follow-ups: {', '.join(result.follow_up_suggestions)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())