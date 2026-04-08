# DevAssist 🤖

> AI agent for developer productivity built with Pydantic AI — features async tool calling, MCP integration, structured outputs, and a CLI interface.

![Python](https://img.shields.io/badge/python-3.12+-blue)
![Pydantic AI](https://img.shields.io/badge/pydantic--ai-latest-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Overview

DevAssist is a CLI AI agent that answers technical questions, searches the web and GitHub, reads local files, and exposes developer utilities via a custom MCP server — all with structured, typed outputs validated by Pydantic.

Built as a portfolio project to demonstrate production-grade agentic patterns with Pydantic AI.

## Features

- 🔍 **Web search** — DuckDuckGo via async `httpx`
- 🐙 **GitHub search** — repos by stars via public API
- 📂 **File reading** — reads and summarizes local files
- 🧮 **Calculator** — safe math expression evaluator
- 🛠️ **MCP tools** — `.gitignore` generator, HTTP status explainer, README template generator
- 💬 **Conversation memory** — maintains context across turns in the CLI
- ⚡ **Streaming** — real-time text output via `run_stream()`
- ✅ **Structured outputs** — all responses validated with Pydantic models

## Architecture

```
devassist/
├── cli.py          # Entry point — rich CLI with conversation history
├── agent.py        # Core agent with async tools (web, GitHub, files)
├── agent_mcp.py    # Streaming demo with MCP tools
├── mcpserver.py    # Custom MCP server (FastMCP over HTTP)
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
      ├── @agent.tool (async)     ← web_search, github_search (httpx + deps injection)
      ├── @agent.tool_plain       ← calculator, file reader, datetime, python info
      └── MCPServerStreamableHTTP ← custom MCP server (gitignore, HTTP status, README)
              │
              ▼
        FastMCP server (HTTP, subprocess managed by CLI)
```

**Key design decisions:**
- `httpx.AsyncClient` lives in `AgentDeps` and is injected into async tools — the recommended production pattern from Pydantic AI docs
- MCP server runs as a managed subprocess started automatically by the CLI
- Empty file content returns `[FILE IS EMPTY]` explicitly to prevent model hallucination
- `MCPServerStreamableHTTP` used instead of `MCPServerStdio` due to a known incompatibility between the MCP SDK's `anyio` subprocess handling and Python 3.14 on Windows

## Tech Stack

| Component | Library |
|---|---|
| Agent framework | `pydantic-ai` |
| LLM | OpenAI `gpt-4o-mini` |
| HTTP client | `httpx` (async) |
| MCP server | `fastmcp` |
| CLI interface | `rich` |
| Config | `python-dotenv` |
| Output validation | `pydantic` v2 |

## Getting Started

### Prerequisites

- Python 3.12+
- OpenAI API key

### Installation

```bash
git clone https://github.com/MatheusM0/devassist
cd devassist

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e .
```

### Configuration

```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

`.env`:
```env
OPENAI_API_KEY=sk-...
```

### Run

```bash
python -m devassist.cli
```

The MCP server starts automatically in the background. No second terminal needed.

## Usage Examples

```
You: Generate a .gitignore for a Python project
You: Search GitHub for the top repos about pydantic-ai
You: What does HTTP 422 mean?
You: Read the file ./pyproject.toml and summarize it
You: What is 1337 * 42?
You: Generate a README template for my project called "Galileu"
```

## What I Learned

- **Dependency injection** in Pydantic AI — `AgentDeps` with `httpx.AsyncClient` passed to async tools via `RunContext`
- **`@agent.tool` vs `@agent.tool_plain`** — when to use `RunContext` and when not to
- **MCP protocol** — building a custom server with `FastMCP` and connecting via `MCPServerStreamableHTTP`
- **Streaming** — `agent.run_stream()` with `stream_text(delta=True)` for real-time output
- **Preventing hallucination at the tool level** — explicit `[FILE IS EMPTY]` return prevents the model from inventing content
- **Python 3.14 + Windows MCP quirk** — `MCPServerStdio` fails due to `anyio` subprocess incompatibility; workaround: HTTP transport

## License

MIT