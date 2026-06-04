"""In-process MCP server exposing testbed tools to Claude Agent SDK.

Stage Two: this file gets a Claude Code orchestrator the ability to call
the simulation as first-class tools (no shell, no subprocess) — letting
it run scenarios, inspect agents, and compare metrics autonomously.

Today: import works even without `claude-agent-sdk` installed, but the
server itself only constructs when the SDK is present. Run
`pip install claude-agent-sdk` to activate.

Usage:
    # Standalone (for testing the server)
    python -m sim.testbed.mcp_server

    # As an MCP server registered with an orchestrator
    from sim.testbed.mcp_server import create_server
    server = create_server()
    # ... pass server into ClaudeAgentOptions(mcp_servers={"testbed": server})
"""
from __future__ import annotations

import json
from typing import Any

from .mcp_tools import TOOLS

try:
    from claude_agent_sdk import create_sdk_mcp_server, tool

    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False


def _wrap_for_mcp(fn):
    """Wrap a sim tool so the MCP layer gets a (args: dict) -> {"content": [...]} shape.

    Sim tools return JSON-shaped dicts directly. MCP wants:
        {"content": [{"type": "text", "text": json.dumps(result)}]}
    """

    async def wrapped(args: dict[str, Any]) -> dict[str, Any]:
        try:
            result = fn(**args)
            return {
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2, default=str)}
                ]
            }
        except Exception as exc:
            return {
                "content": [
                    {"type": "text", "text": f"Error in {fn.__name__}: {exc!r}"}
                ],
                "isError": True,
            }

    wrapped.__name__ = fn.__name__
    wrapped.__doc__ = fn.__doc__
    return wrapped


def _infer_schema(fn) -> dict[str, str]:
    """Best-effort param schema from function annotations.

    Stage Two enhancement: replace with proper JSON Schema generation
    (e.g. via pydantic) once the tool surface stabilizes.
    """
    import inspect
    sig = inspect.signature(fn)
    schema: dict[str, str] = {}
    for name, param in sig.parameters.items():
        ann = param.annotation
        if ann is int:
            schema[name] = "int"
        elif ann is str:
            schema[name] = "str"
        elif ann is float:
            schema[name] = "float"
        elif ann is bool:
            schema[name] = "bool"
        else:
            schema[name] = "str"  # fallback
    return schema


def create_server():
    """Build the in-process MCP server exposing all testbed tools.

    Returns:
        An MCP server object suitable for ClaudeAgentOptions.mcp_servers.

    Raises:
        RuntimeError: if claude-agent-sdk is not installed.
    """
    if not _SDK_AVAILABLE:
        raise RuntimeError(
            "claude-agent-sdk is not installed. Run `pip install claude-agent-sdk` "
            "to enable the MCP server. Until then, tools in mcp_tools.py "
            "are importable as plain Python functions."
        )

    decorated = []
    for tool_name, fn in TOOLS.items():
        decorated.append(
            tool(
                tool_name,
                (fn.__doc__ or tool_name).strip().split("\n")[0],
                _infer_schema(fn),
            )(_wrap_for_mcp(fn))
        )
    return create_sdk_mcp_server(name="nihonbashi-testbed", tools=decorated)


def _ascii_list_tools() -> str:
    lines = ["Registered testbed tools:"]
    for name, fn in TOOLS.items():
        first = (fn.__doc__ or "").strip().split("\n")[0]
        lines.append(f"  - {name}: {first}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_ascii_list_tools())
    if not _SDK_AVAILABLE:
        print()
        print("claude-agent-sdk NOT installed. Tools work as plain Python:")
        print("    from sim.testbed.mcp_tools import list_scenarios")
        print("    print(list_scenarios())")
    else:
        print()
        print("claude-agent-sdk detected. Use create_server() to register.")
