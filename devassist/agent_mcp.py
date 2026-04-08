from __future__ import annotations

import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

load_dotenv()

# Conecta ao server HTTP em vez de subprocess stdio
mcp_server = MCPServerStreamableHTTP("http://127.0.0.1:8000/mcp")

agent = Agent(
    model="openai:gpt-4o-mini",
    toolsets=[mcp_server],
    instructions=(
        "You are DevAssist, a developer productivity agent. "
        "Use your tools to help developers with practical tasks. "
        "Be concise and helpful."
    ),
)


async def ask_with_streaming(question: str) -> None:
    print(f"\nQ: {question}")
    print("A: ", end="", flush=True)

    async with agent:
        async with agent.run_stream(question) as stream:
            async for text in stream.stream_text(delta=True):
                print(text, end="", flush=True)

    print()


async def main() -> None:
    questions = [
        "Generate a .gitignore for a Python project.",
        "What does HTTP status 422 mean?",
        "Generate a README template for a project called 'DevAssist' that is an AI agent for developer productivity, written in Python.",
    ]

    print("=" * 60)
    print("DevAssist — MCP + Streaming Demo")
    print("=" * 60)

    for q in questions:
        await ask_with_streaming(q)
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())