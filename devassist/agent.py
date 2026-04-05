from __future__ import annotations

import asyncio
from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from devassist.models import AnswerResult
from devassist.tools import calculate, get_current_datetime, get_python_info

load_dotenv()


# --- Dependencies ---
# Dependency injection: dados e contexto passados ao agent em runtime
@dataclass
class AgentDeps:
    user_name: str
    session_id: str


# --- Agent ---
agent = Agent(
    model="openai:gpt-4o-mini",
    deps_type=AgentDeps,
    output_type=AnswerResult,
    instructions=(
        "You are DevAssist, an AI agent for developer productivity. "
        "Answer technical questions clearly and concisely. "
        "Always provide a confidence score honestly. "
        "Suggest relevant follow-up questions when appropriate."
    ),
)


# --- Tools ---
# @agent.tool tem acesso ao RunContext (deps, histórico, etc.)
@agent.tool
def get_user_context(ctx: RunContext[AgentDeps]) -> str:
    """Get the current user's name and session information."""
    return f"User: {ctx.deps.user_name} | Session: {ctx.deps.session_id}"


# @agent.tool_plain NÃO precisa de RunContext — para tools simples
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
    """
    Evaluate a mathematical expression.

    Args:
        expression: A math expression like '2 + 2' or '100 / 4'
    """
    return calculate(expression)


# --- Runner ---
async def ask(question: str, user_name: str = "Developer") -> AnswerResult:
    """Run the agent with a question and return a structured answer."""
    deps = AgentDeps(user_name=user_name, session_id="session-001")
    result = await agent.run(question, deps=deps)
    return result.output


async def main() -> None:
    questions = [
        "What Python version am I running?",
        "What is 1337 * 42?",
        "How do I reverse a list in Python?",
    ]

    for question in questions:
        print(f"\n{'='*60}")
        print(f"Q: {question}")
        answer = await ask(question, user_name="Matheus")
        print(f"A: {answer.answer}")
        print(f"Confidence: {answer.confidence:.0%}")
        if answer.sources:
            print(f"Sources: {', '.join(answer.sources)}")
        if answer.follow_up_suggestions:
            print(f"Follow-ups: {', '.join(answer.follow_up_suggestions)}")


if __name__ == "__main__":
    asyncio.run(main())