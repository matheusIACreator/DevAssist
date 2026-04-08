# DevAssist 🤖

> AI agent for developer productivity built with Pydantic AI — features async tool calling, dual MCP integration (custom server + Firecrawl), structured outputs, and a CLI interface.

![Python](https://img.shields.io/badge/python-3.12+-blue)
![Pydantic AI](https://img.shields.io/badge/pydantic--ai-latest-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Overview

DevAssist is a CLI AI agent that answers technical questions, searches and scrapes the web with full page content, searches GitHub, reads local files, and exposes developer utilities via a custom MCP server — all with structured, typed outputs validated by Pydantic.

Built as a portfolio project to demonstrate production-grade agentic patterns with Pydantic AI.

## Features

- 🔥 **Web scraping** — full page content via Firecrawl MCP (search + scrape any URL)
- 🔍 **Web search** — DuckDuckGo fallback via async `httpx`
- 🐙 **GitHub search** — repos by stars via public API
- 📂 **File reading** — reads and summarizes local files
- 🧮 **Calculator** — safe math expression evaluator
- 🛠️ **MCP tools** — `.gitignore` generator, HTTP status explainer, README template generator
- 💬 **Conversation memory** — maintains context across turns in the CLI
- ✅ **Structured outputs** — all responses validated with Pydantic models

## Architecture

```
devassist/
├── cli.py          # Entry point — rich CLI with conversation history
├── agent.py        # Core agent with async tools (web, GitHub, files)
├── agent_mcp.py    # Streaming demo with MCP tools
├── mcpserver.py    # Custom MCP server (FastMCP via stdio)
├── models.py       # Pydantic output models (AnswerResult, SearchResult, GitHubRepo)
└── tools.py        # Pure functions used by agent tools
```

### How it works

```
User input (CLI)
      │
      ▼
  Pydantic AI Agent (gpt-4o-mini)
      │
      ├── @agent.tool (async)      ← web_search, github_search (httpx + deps injection)
      ├── @agent.tool_plain        ← calculator, file reader, datetime, python info
      ├── MCPServerStdio           ← custom MCP server (gitignore, HTTP status, README)
      └── MCPServerStdio           ← Firecrawl MCP (search + full page scraping)
              │
              ▼
        Both servers managed automatically via `async with agent:`
```

**Key design decisions:**
- `httpx.AsyncClient` lives in `AgentDeps` and is injected into async tools via `RunContext` — the recommended production pattern from Pydantic AI docs
- Both MCP servers run as stdio subprocesses managed automatically by the CLI — no separate terminals needed
- Firecrawl replaces shallow snippet search with full page content — the agent reads and understands pages, not just links
- Empty file content returns `[FILE IS EMPTY]` explicitly to prevent model hallucination
- Custom `mcpserver.py` must be launched with `transport="stdio"` explicitly — omitting this causes a silent timeout on Windows (the server starts but never responds to the MCP handshake)

## Tech Stack

| Component | Library |
|---|---|
| Agent framework | `pydantic-ai` |
| LLM | OpenAI `gpt-4o-mini` |
| HTTP client | `httpx` (async) |
| Custom MCP server | `fastmcp` |
| Web scraping MCP | `firecrawl-mcp` (via `npx`) |
| CLI interface | `rich` |
| Config | `python-dotenv` |
| Output validation | `pydantic` v2 |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js (required for Firecrawl MCP via `npx`)
- OpenAI API key
- Firecrawl API key (free tier at [firecrawl.dev](https://www.firecrawl.dev))

### Installation

```bash
git clone [https://github.com/MatheusM0/devassist](https://github.com/matheusIACreator/DevAssist.git)
cd devassist

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

pip install -e .
```

### Configuration

```bash
cp .env.example .env
# Add your keys to .env
```

`.env`:
```env
OPENAI_API_KEY=sk-...
FIRECRAWL_API_KEY=fc-...
```

### Run

```bash
python -m devassist.cli
```

Both MCP servers start automatically. No extra terminals needed.

## Usage Examples

```
You: Scrape https://pypi.org/project/pydantic-ai/ and tell me the latest version
You: Search for "FastAPI best practices 2025" and summarize the top findings
You: Search GitHub for the top repos about pydantic-ai
You: Generate a .gitignore for a Python project
You: What does HTTP 422 mean?
You: Read the file ./pyproject.toml and summarize it
You: What is 1337 * 42?
You: Generate a README template for my project called "Galileu"
```

## What I Learned

- **Dependency injection** in Pydantic AI — `AgentDeps` with `httpx.AsyncClient` passed to async tools via `RunContext`
- **`@agent.tool` vs `@agent.tool_plain`** — when to use `RunContext` and when not to
- **MCP protocol** — building a custom server with `FastMCP` and connecting external servers like Firecrawl via `MCPServerStdio`
- **Multiple MCP toolsets** — composing `toolsets=[mcp_devassist, mcp_firecrawl]` to give the agent capabilities from multiple sources simultaneously
- **Preventing hallucination at the tool level** — explicit `[FILE IS EMPTY]` return prevents the model from inventing content
- **stdio transport default matters** — `FastMCP` defaults to `streamable-http`; when used as a subprocess by Pydantic AI, it must be launched with `transport="stdio"` explicitly or the MCP handshake silently times out

## License

MIT
