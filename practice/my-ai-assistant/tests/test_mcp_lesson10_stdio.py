"""Lesson 10 MCP stdio integration tests: real local MCP subprocess, no LLM API.

Requires the pinned MCP Python SDK (requirements-lesson10.txt).
Unlike test_mcp_lesson10.py, these tests actually initialize an MCP session.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "mcp_lesson10_server.py"
HAS_MCP = importlib.util.find_spec("mcp") is not None


@unittest.skipUnless(HAS_MCP, "MCP SDK unavailable; install requirements-lesson10.txt")
class MCPStdioIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_tools_resource_prompt_and_error(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER)],
            cwd=str(ROOT),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()  # A real protocol handshake.

                listed = await session.list_tools()
                self.assertEqual(
                    {tool.name for tool in listed.tools},
                    {"add_numbers", "find_notice"},
                )

                addition = await session.call_tool(
                    "add_numbers", arguments={"a": 12, "b": 30},
                )
                self.assertFalse(addition.isError, addition)
                payload = addition.structuredContent or addition.content
                self.assertIn("42", str(payload))

                notice = await session.call_tool(
                    "find_notice", arguments={"query": "과제 제출"},
                )
                self.assertFalse(notice.isError, notice)
                self.assertIn("lesson04_notice.md", str(notice.structuredContent or notice.content))

                resource = await session.read_resource("lesson10://public-notice")
                self.assertTrue(resource.contents)
                self.assertIn("과제 제출", " ".join(
                    item.text for item in resource.contents if hasattr(item, "text")
                ))

                prompt = await session.get_prompt(
                    "explain_topic", arguments={"topic": "MCP"},
                )
                self.assertTrue(prompt.messages)
                self.assertIn("MCP", " ".join(
                    message.content.text
                    for message in prompt.messages
                    if hasattr(message.content, "text")
                ))

                rejected = await session.call_tool(
                    "add_numbers", arguments={"a": 100001, "b": 1},
                )
                self.assertTrue(rejected.isError, rejected)


if __name__ == "__main__":
    unittest.main()
