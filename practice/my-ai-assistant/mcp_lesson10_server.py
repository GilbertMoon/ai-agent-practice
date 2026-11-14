"""Lesson 10 real local MCP server (stdio, MCP Python SDK v1).

Never print to stdout in server process: stdout is reserved for MCP messages.
No API keys, network operations, arbitrary file paths or write tools.
"""
from mcp.server.fastmcp import FastMCP
from mcp_lesson10_logic import add_numbers as safe_add, find_notice as safe_find
from mcp_lesson10_logic import public_notice, lesson_prompt

mcp = FastMCP("Lesson10ReadOnly")


@mcp.tool()
def add_numbers(a: int, b: int) -> dict:
    """Add two bounded integers (no side effects)."""
    return safe_add(a, b)


@mcp.tool()
def find_notice(query: str) -> dict:
    """Search only the bundled public teaching notice."""
    return safe_find(query)


@mcp.resource("lesson10://public-notice")
def get_public_notice() -> str:
    """Read the bundled teaching notice, never arbitrary local files."""
    return public_notice()


@mcp.prompt()
def explain_topic(topic: str) -> str:
    """Return a reusable teaching prompt, not an LLM answer."""
    return lesson_prompt(topic)


if __name__ == "__main__":
    mcp.run(transport="stdio")
