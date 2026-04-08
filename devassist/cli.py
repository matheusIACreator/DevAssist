"""
DevAssist CLI

Interface interativa com MCP via stdio + Firecrawl integration.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio

from devassist.models import GitHubRepo, SearchResult
from devassist.tools import calculate, get_current_datetime, get_python_info, read_local_file

load_dotenv()

console = Console()


# --- MCP Servers ---
mcp_devassist = MCPServerStdio(
    sys.executable,
    args=["-m", "devassist.mcpserver", "stdio"],
    timeout=15,
)

mcp_firecrawl = MCPServerStdio(
    "npx",
    args=["-y", "firecrawl-mcp"],
    env={**os.environ, "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")},
    timeout=30,
)


# --- Deps ---
@dataclass
class AgentDeps:
    user_name: str
    http_client: httpx.AsyncClient


# --- Agent ---
agent = Agent(
    model="openai:gpt-4o-mini",
    deps_type=AgentDeps,
    toolsets=[mcp_devassist, mcp_firecrawl],
    instructions=(
        "You are DevAssist, an AI agent for developer productivity. "
        "Answer technical questions clearly. Use tools when relevant. "
        "For web research and scraping full page content, prefer firecrawl tools. "
        "For quick searches use web_search. "
        "Format code blocks with markdown when showing code."
    ),
)


# --- Tools ---
@agent.tool
def get_user_context(ctx: RunContext[AgentDeps]) -> str:
    """Get the current user's name."""
    return f"User: {ctx.deps.user_name}"


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
    """Read the contents of a local file. Args: file_path: path to the file."""
    return read_local_file(file_path)


@agent.tool
async def web_search(ctx: RunContext[AgentDeps], query: str) -> list[SearchResult]:
    """Search the web using DuckDuckGo. Args: query: search terms."""
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
    try:
        response = await ctx.deps.http_client.get(
            "https://api.duckduckgo.com/", params=params, timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("RelatedTopics", [])[:5]:
            if "Text" in item and "FirstURL" in item:
                results.append(SearchResult(
                    title=item.get("Text", "")[:80],
                    snippet=item.get("Text", ""),
                    url=item.get("FirstURL", ""),
                ))
        return results or [SearchResult(title="No results", snippet="No results found.", url="")]
    except Exception as e:
        return [SearchResult(title="Error", snippet=str(e), url="")]


@agent.tool
async def github_search(
    ctx: RunContext[AgentDeps], query: str, max_results: int = 5
) -> list[GitHubRepo]:
    """Search GitHub repositories. Args: query: search terms."""
    try:
        response = await ctx.deps.http_client.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "per_page": min(max_results, 10)},
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
    except Exception:
        return []


# --- UI helpers ---
def print_welcome() -> None:
    console.print(Panel(
        Text.assemble(
            ("DevAssist", "bold cyan"),
            " — AI Agent for Developer Productivity\n\n",
            ("Type your question or command.\n", "dim"),
            ("Commands: ", "bold"),
            ("exit", "bold red"), " to quit  •  ",
            ("clear", "bold yellow"), " to clear screen",
        ),
        border_style="cyan",
    ))


# --- CLI loop ---
async def run_cli() -> None:
    print_welcome()

    user_name = Prompt.ask("\n[cyan]What's your name?[/cyan]", default="Developer")
    console.print(f"\n[green]Hey {user_name}! Ask me anything.[/green]\n")

    history = []

    async with httpx.AsyncClient() as http_client:
        deps = AgentDeps(user_name=user_name, http_client=http_client)

        async with agent:
            while True:
                try:
                    question = Prompt.ask("[bold cyan]You[/bold cyan]")
                except (KeyboardInterrupt, EOFError):
                    break

                question = question.strip()
                if not question:
                    continue
                if question.lower() in ("exit", "quit", "q"):
                    break
                if question.lower() == "clear":
                    console.clear()
                    print_welcome()
                    continue

                console.print()

                with console.status("[dim]Thinking...[/dim]", spinner="dots"):
                    result = await agent.run(
                        question,
                        deps=deps,
                        message_history=history,
                    )

                md = Markdown(result.output)
                console.print(Panel(
                    md,
                    border_style="green",
                    title="[bold green]DevAssist[/bold green]",
                ))

                history = result.all_messages()
                console.print(Rule(style="dim"))

    console.print("\n[dim]Goodbye! 👋[/dim]\n")


def main() -> None:
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()