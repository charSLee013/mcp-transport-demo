from __future__ import annotations

"""
Streamable HTTP client that connects to the demo server and prints a full trace:
- HTTP request/response headers and bodies (POST /mcp, GET /mcp stream)
- JSON-RPC flow (initialize -> list tools -> call tool/stream)

Run (from repo root):
  # 1) In one terminal, start the server
  PYTHONPATH=src uv run python examples/snippets/servers/streamable_progress_demo.py

  # 2) In another terminal, run the client
  PYTHONPATH=src uv run python examples/snippets/clients/streamable_progress_client.py
"""

import anyio
from datetime import datetime
from typing import Any

import httpx
import json
from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.message import SessionMessage
from mcp.shared.session import RequestResponder
from mcp.types import JSONRPCMessage


def now() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


async def message_tap(
    msg: RequestResponder[types.ServerRequest, types.ClientResult]
    | types.ServerNotification
    | Exception,
) -> None:
    # Print every incoming message for full transparency
    match msg:
        case RequestResponder():
            print(f"[{now()}] <- server request: {type(msg.request.root).__name__} id={msg.request_id}")
        case types.ServerNotification(root=types.LoggingMessageNotification(params=params)):
            print(f"[{now()}] <- notification (logging):")
            print(_maybe_pretty_json(types.ServerNotification(
                types.LoggingMessageNotification(params=params)
            ).model_dump_json(by_alias=True)))
        case types.ServerNotification(root=types.ProgressNotification(params=params)):
            print(f"[{now()}] <- notification (progress):")
            print(_maybe_pretty_json(types.ServerNotification(
                types.ProgressNotification(params=params)
            ).model_dump_json(by_alias=True)))
            print(f"[{now()}] ~~ progress callback: {params.progress}/{params.total} {params.message or ''}")
        case types.ServerNotification(root=root):
            print(f"[{now()}] <- notification (other):")
            try:
                print(_maybe_pretty_json(types.ServerNotification(root).model_dump_json(by_alias=True)))
            except Exception:
                print(str(root))
        case Exception() as e:
            print(f"[{now()}] !! incoming exception: {e}")


def _maybe_pretty_json(body: str) -> str:
    try:
        parsed = json.loads(body)
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        return body


def print_sep(title: str) -> None:
    print(f"\n-------<{title}-------")


def make_logging_http_client_factory():
    async def on_request(request: httpx.Request) -> None:
        body_preview = request.content if request.content else b""
        body_str = body_preview.decode("utf-8", errors="replace") if body_preview else ""
        pretty = _maybe_pretty_json(body_str) if body_str else ""
        hints = {
            "mcp-session-id": "existing session identifier",
            "mcp-protocol-version": "negotiated protocol version",
            "content-type": "JSON body for POST",
            "last-event-id": "resumption token for SSE replay",
        }
        print(f"[{now()}] >>> REQUEST {request.method} {request.url}")
        if request.headers:
            print("  Headers (filtered — hint):")
        for k, v in request.headers.items():
            lk = k.lower()
            if lk in {"host", "accept-encoding", "user-agent"}:
                continue
            hint = f" — {hints[lk]}" if lk in hints else ""
            print(f"    {k}: {v}{hint}")
        if pretty:
            print("  Body:\n" + pretty)
        print()

    async def on_response(response: httpx.Response) -> None:
        req = response.request
        ctype = response.headers.get("content-type", "")
        is_sse = "text/event-stream" in ctype
        body_str = ""
        if not is_sse:
            try:
                content = await response.aread()
                body_str = content.decode("utf-8", errors="replace")
            except Exception:
                body_str = "<streamed>"
        hints = {
            "mcp-session-id": "new session id negotiated",
            "mcp-protocol-version": "server-advertised protocol version",
            "content-type": "payload media type",
            "transfer-encoding": "chunked = streaming",
            "cache-control": "disable caching for streaming",
            "x-accel-buffering": "no disables proxy buffering (SSE)",
        }
        print(f"[{now()}] <<< RESPONSE {response.status_code} {response.reason_phrase} ({req.method} {req.url})")
        if response.headers:
            print("  Headers (filtered — hint):")
        for k, v in response.headers.items():
            lk = k.lower()
            if lk in {"date", "server", "content-length"} and not is_sse:
                continue
            hint = f" — {hints[lk]}" if lk in hints else ""
            print(f"    {k}: {v}{hint}")
        if body_str:
            if "application/json" in ctype:
                print("  Body (pretty JSON):\n" + _maybe_pretty_json(body_str))
            else:
                snippet = body_str.strip().splitlines()
                if snippet:
                    print("  Body:\n  " + snippet[0])
        if is_sse:
            print("  Body: <stream (SSE handled by transport)>")
        print()

    def factory(
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
    ) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=headers,
            timeout=timeout or httpx.Timeout(30.0),
            auth=auth,
            follow_redirects=True,
            event_hooks={
                "request": [on_request],
                "response": [on_response],
            },
        )

    return factory


async def main() -> None:
    url = "http://127.0.0.1:8000/mcp"
    print_sep("Connect Streamable HTTP")
    print(f"[{now()}] Connecting -> {url}")

    factory = make_logging_http_client_factory()
    async with streamablehttp_client(
        url,
        httpx_client_factory=factory,
    ) as (read, write, get_session_id):
        async with ClientSession(read, write, message_handler=message_tap) as session:
            print_sep("Initialize")
            init = await session.initialize()
            print(f"[{now()}] << initialize.result protocol={init.protocolVersion}")
            sid = get_session_id()
            if sid:
                print(f"[{now()}] !! session id negotiated: {sid}")

            print_sep("List Tools")
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            print(f"[{now()}] << tools/list.result tools={tool_names}")

            print_sep("Stream Demo")
            async def on_progress(p: float, t: float | None, msg: str | None) -> None:
                print(f"[{now()}] ~~ progress callback: {p}/{t} {msg or ''}")

            stream_res = await session.call_tool(
                name="stream_demo",
                arguments={"seconds": 1.5, "steps": 4},
                progress_callback=on_progress,
            )
            if stream_res.structuredContent is not None:
                print(f"[{now()}] << stream_demo.structured {stream_res.structuredContent}")

            print_sep("Call Tool: calculator")
            result = await session.call_tool(
                name="calculator",
                arguments={"a": 7, "b": 4, "operation": "add"},
            )
            if result.content:
                block = result.content[0]
                if isinstance(block, types.TextContent):
                    print(f"[{now()}] << tools/call.result text={block.text}")
            if result.structuredContent is not None:
                print(f"[{now()}] << tools/call.structured {result.structuredContent}")


if __name__ == "__main__":
    anyio.run(main)
