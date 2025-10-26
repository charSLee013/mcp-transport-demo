from __future__ import annotations

"""
Streamable HTTP demo server exposing the same tools as the SSE example.

Run:
  PYTHONPATH=src uv run python examples/snippets/servers/streamable_progress_demo.py

Endpoint: http://127.0.0.1:8000/mcp  (POST / GET for StreamableHTTP)
"""

import asyncio
import time
from typing import Literal

from mcp.server.fastmcp import Context, FastMCP


mcp = FastMCP(
    name="Streamable Progress Demo",
    streamable_http_path="/mcp",
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
    """Emit log + progress notifications before returning a result."""
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
    # Start Streamable HTTP transport (serves /mcp for POST/GET)
    mcp.run(transport="streamable-http")
