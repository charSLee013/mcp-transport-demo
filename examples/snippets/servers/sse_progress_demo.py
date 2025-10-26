from __future__ import annotations

"""
SSE demo server exposing a simple calculator tool (no progress).

Run:
  PYTHONPATH=src uv run python examples/snippets/servers/sse_progress_demo.py

SSE endpoint:  http://127.0.0.1:8000/sse
Message path:  http://127.0.0.1:8000/messages/
"""

import asyncio
import time
from typing import Literal

from mcp.server.fastmcp import Context, FastMCP


mcp = FastMCP(
    name="SSE Progress Demo",
    # Defaults: host=127.0.0.1, port=8000, sse_path="/sse", message_path="/messages/"
)


@mcp.tool(title="Calculator")
def calculator(a: float, b: float, operation: Literal["add", "subtract"]) -> str:
    """Execute a basic calculation."""
    if operation == "add":
        return f"结果: {a + b}"
    elif operation == "subtract":
        return f"结果: {a - b}"
    else:
        return "不支持的运算"


@mcp.tool(title="Stream Demo")
async def stream_demo(seconds: float = 2.0, steps: int = 5, ctx: Context | None = None) -> dict:
    """Emit log + progress notifications over SSE before returning a result.

    Args:
        seconds: total duration (simulated)
        steps: number of progress steps
    """
    start = time.perf_counter()
    if ctx is not None:
        await ctx.info(f"stream started: {steps} steps / {seconds}s total")
    for i in range(steps):
        await asyncio.sleep(max(0.0, seconds / steps))
        pct = int(((i + 1) / steps) * 100)
        if ctx is not None:
            await ctx.info(f"step {i + 1}/{steps}")
            await ctx.report_progress(pct, 100, f"step {i + 1}")
    elapsed = round(time.perf_counter() - start, 3)
    if ctx is not None:
        await ctx.info("stream finished")
    return {"status": "done", "steps": steps, "seconds": seconds, "elapsed": elapsed}


if __name__ == "__main__":
    # Start SSE transport (serves /sse and /messages/)
    mcp.run("sse")
