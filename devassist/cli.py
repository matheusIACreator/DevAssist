"""
DevAssist CLI

Interface interativa que arranca o MCP server automaticamente.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import time
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
from pydantic_ai.mcp import MCPServerStreamableHTTP

from devassist.models import GitHubRepo, SearchResult
from devassist.tools import calculate, get_current_datetime, get_python_info, read_local_file

load_dotenv()

console = Console()

MCP_URL = "http://127.0.0.1:8000/mcp"
MCP_HEALTH_URL = "http://127.0.0.1:8000"


# --- MCP Server ---
mcp_server = MCPServerStreamableHTTP(MCP_URL)


# --- Deps ---
@dataclass
class AgentDeps:
    user_name: str
    http_client: httpx.AsyncClient


# --- Agent ---
agent = Agent(
    model="openai:gpt-4o-mini",
    deps_type=AgentDeps,
    toolsets=[mcp_server],
    instructions=(
        "You are DevAssist, an AI agent for developer productivity. "
        "Answer technical questions clearly. Use tools when relevant. "
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


# --- MCP Server lifecycle ---
def start_mcp_server() -> subprocess.Popen:
    """Arranca o MCP server como subprocess em background."""
    process = subprocess.Popen(
        [sys.executable, "-m", "devassist.mcpserver"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process


def wait_for_mcp_server(timeout: int = 15) -> bool:
    """Aguarda o MCP server ficar disponível."""
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(
                urllib.request.Request(
                    MCP_URL,
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    data=b"{}",
                ),
                timeout=1,
            )
        except urllib.error.HTTPError:
            # Qualquer resposta HTTP (mesmo erro 4xx) significa que o server está up
            return True
        except Exception:
            time.sleep(0.3)
    return False

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
    # Arranca o MCP server em background
    with console.status("[dim]Starting MCP server...[/dim]", spinner="dots"):
        mcp_process = start_mcp_server()
        ready = wait_for_mcp_server(timeout=10)

    if not ready:
        console.print("[red]Failed to start MCP server. Exiting.[/red]")
        mcp_process.terminate()
        sys.exit(1)

    console.print("[dim]MCP server ready.[/dim]\n")

    try:
        asyncio.run(run_cli())
    finally:
        # Garante que o server é terminado ao sair
        mcp_process.terminate()
        mcp_process.wait()


if __name__ == "__main__":
    main()