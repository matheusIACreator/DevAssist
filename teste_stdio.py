import asyncio
import sys
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

load_dotenv()

server = MCPServerStdio(
    sys.executable,
    args=["-m", "devassist.mcpserver", "stdio"],
    timeout=15,
)

agent = Agent(
    model="openai:gpt-4o-mini",
    toolsets=[server],
    instructions="Use your tools to help.",
)

async def main():
    async with agent:
        result = await agent.run("Generate a .gitignore for Python.")
        print(result.output)

asyncio.run(main())