from __future__ import annotations

"""
SSE client that connects to the demo server and prints a full trace:
- HTTP request/response headers and bodies (SSE GET + POST /messages)
- JSON-RPC flow (initialize -> list tools -> call tool)

Run (from repo root):
  # 1) In one terminal, start the server
  PYTHONPATH=src uv run python examples/snippets/servers/sse_progress_demo.py

  # 2) In another terminal, run the client
  PYTHONPATH=src uv run python examples/snippets/clients/sse_progress_client.py
"""

import anyio
from datetime import datetime
from typing import Any

import httpx
import json
from mcp import ClientSession, types
from mcp.client.sse import sse_client  # kept for reference
from mcp.shared._httpx_utils import McpHttpClientFactory
from anyio.streams.memory import (
    MemoryObjectReceiveStream,
    MemoryObjectSendStream,
)
from mcp.shared.message import SessionMessage
from mcp.types import JSONRPCMessage
from urllib.parse import urljoin, urlparse


def now() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


async def message_tap(
    msg: "types.RequestResponder[types.ServerRequest, types.ClientResult] | types.ServerNotification | Exception",
) -> None:
    # Print every incoming message for full transparency
    match msg:
        case types.RequestResponder():
            print(f"[{now()}] <- server request: {type(msg.request.root).__name__} id={msg.request_id}")
        case types.ServerNotification(root=types.LoggingMessageNotification(params=params)):
            print(f"[{now()}] <- SSE notification (logging):")
            print(
                _maybe_pretty_json(
                    types.ServerNotification(
                        types.LoggingMessageNotification(params=params)
                    ).model_dump_json(by_alias=True)
                )
            )
        case types.ServerNotification(root=types.ProgressNotification(params=params)):
            print(f"[{now()}] <- SSE notification (progress):")
            print(
                _maybe_pretty_json(
                    types.ServerNotification(
                        types.ProgressNotification(params=params)
                    ).model_dump_json(by_alias=True)
                )
            )
            # Also show the callback-style view
            print(f"[{now()}] ~~ progress callback: {params.progress}/{params.total} {params.message or ''}")
        case types.ServerNotification(root=root):
            # Unknown/other notification types – print full JSON
            print(f"[{now()}] <- SSE notification (other):")
            try:
                print(_maybe_pretty_json(types.ServerNotification(root).model_dump_json(by_alias=True)))
            except Exception:
                print(str(root))
        case Exception() as e:
            print(f"[{now()}] !! incoming exception: {e}")


def _fmt_headers_filtered(headers: httpx.Headers, *, role: str) -> str:
    # Drop noisy headers
    drop = {"host", "accept", "accept-encoding", "user-agent"}
    allow_req = {"connection", "cache-control", "content-type"}
    allow_res = {"connection", "cache-control", "content-type", "transfer-encoding", "x-accel-buffering", "content-length"}
    lines: list[str] = []
    for k, v in headers.items():
        lk = k.lower()
        if lk in drop:
            continue
        if role == "request" and lk not in allow_req:
            continue
        if role == "response" and lk not in allow_res:
            continue
        lines.append(f"    {k}: {v}")
    return "\n".join(lines)


def _maybe_pretty_json(body: str) -> str:
    try:
        import json

        parsed = json.loads(body)
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        return body


def print_sep(title: str) -> None:
    print(f"\n-------<{title}-------")


def make_logging_http_client_factory() -> McpHttpClientFactory:
    async def on_request(request: httpx.Request) -> None:
        body_preview = request.content if request.content else b""
        body_str = body_preview.decode("utf-8", errors="replace") if body_preview else ""
        pretty = _maybe_pretty_json(body_str) if body_str else ""
        # Header hints (filtered keys only)
        hints = {
            "cache-control": "no-store disables caching for streams",
            "connection": "keep-alive keeps TCP open for streaming",
            "content-type": "JSON body for POST",
        }
        print(f"[{now()}] >>> REQUEST {request.method} {request.url}")
        print("  Headers (filtered — hint):")
        for k, v in request.headers.items():
            hk = k.lower()
            if hk in {"host", "accept", "accept-encoding", "user-agent"}:
                continue
            if hk not in {"connection", "cache-control", "content-type"}:
                continue
            hint = f" — {hints[hk]}" if hk in hints else ""
            print(f"    {k}: {v}{hint}")
        if pretty:
            print("  Body:\n" + pretty)
        print()

    async def on_response(response: httpx.Response) -> None:
        req = response.request
        # Avoid consuming SSE streaming body; only log headers for GET /sse
        log_body = not (req.method == "GET" and "/sse" in str(req.url))
        body_str = ""
        if log_body:
            try:
                content = await response.aread()
                body_str = content.decode("utf-8", errors="replace")
            except Exception:
                body_str = "<streamed>"
        # Header hints emphasize SSE/streaming semantics (filtered keys only)
        hints = {
            "content-type": "payload media type",
            "cache-control": "disable caching for streaming",
            "connection": "keep-alive keeps stream open",
            "x-accel-buffering": "no disables proxy buffering (SSE)",
            "transfer-encoding": "chunked = streaming",
            "content-length": "size for non-stream",
        }
        print(f"[{now()}] <<< RESPONSE {response.status_code} {response.reason_phrase} ({req.method} {req.url})")
        print("  Headers (filtered — hint):")
        for k, v in response.headers.items():
            hk = k.lower()
            if hk not in {"connection", "cache-control", "content-type", "transfer-encoding", "x-accel-buffering", "content-length"}:
                continue
            hint = f" — {hints[hk]}" if hk in hints else ""
            print(f"    {k}: {v}{hint}")
        ctype = response.headers.get("content-type", "")
        if body_str and "application/json" in ctype:
            print("  Body (pretty JSON):\n" + _maybe_pretty_json(body_str))
        elif body_str:
            oneline = body_str.strip().splitlines()[0] if body_str.strip() else ""
            if oneline:
                print("  Body:\n  " + oneline)
        print()

    def factory(headers: dict[str, str] | None = None,
                timeout: httpx.Timeout | None = None,
                auth: httpx.Auth | None = None) -> httpx.AsyncClient:
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


class RawSSEClient:
    def __init__(self, url: str, timeout: float = 5, sse_read_timeout: float = 300):
        self.url = url
        self.timeout = timeout
        self.sse_read_timeout = sse_read_timeout
        self._client: httpx.AsyncClient | None = None
        self._read_stream_writer: MemoryObjectSendStream[SessionMessage | Exception]
        self._read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
        self._write_stream: MemoryObjectSendStream[SessionMessage]
        self._write_stream_reader: MemoryObjectReceiveStream[SessionMessage]

        self._read_stream_writer, self._read_stream = anyio.create_memory_object_stream(0)
        self._write_stream, self._write_stream_reader = anyio.create_memory_object_stream(0)

    async def _post_writer(self, endpoint_url: str):
        assert self._client is not None
        async with self._write_stream_reader:
            async for session_message in self._write_stream_reader:
                body = session_message.message.model_dump(by_alias=True, mode="json", exclude_none=True)
                print(f"[{now()}] >>> REQUEST POST {endpoint_url}")
                print("  Headers (filtered — hint):")
                print("    connection: keep-alive — keep-alive keeps TCP open for streaming")
                print("    content-type: application/json — JSON body for POST")
                print("  Body:\n" + _maybe_pretty_json(json.dumps(body, ensure_ascii=False)))
                resp = await self._client.post(endpoint_url, json=body)
                print(f"[{now()}] <<< RESPONSE {resp.status_code} {resp.reason_phrase} (POST {endpoint_url})")
                print("  Headers (filtered — hint):")
                if "content-length" in resp.headers:
                    print(f"    content-length: {resp.headers['content-length']} — size for non-stream")
                print("  Body:\n  " + (resp.text.strip().splitlines()[0] if resp.text else ""))
        await self._write_stream.aclose()

    async def _sse_reader(self):
        assert self._client is not None
        # GET /sse with streaming
        print(f"[{now()}] >>> REQUEST GET {self.url}")
        print("  Headers (filtered — hint):")
        print("    connection: keep-alive — keep-alive keeps TCP open for streaming")
        print("    cache-control: no-store — no-store disables caching for streams")
        async with self._client.stream("GET", self.url, timeout=httpx.Timeout(self.timeout, read=self.sse_read_timeout)) as resp:
            print(f"[{now()}] <<< RESPONSE {resp.status_code} {resp.reason_phrase} (GET {self.url})")
            print("  Headers (filtered — hint):")
            for key in ["connection", "transfer-encoding", "cache-control", "content-type", "x-accel-buffering"]:
                if key in resp.headers:
                    hints = {
                        "connection": "keep-alive keeps stream open",
                        "transfer-encoding": "chunked = streaming",
                        "cache-control": "disable caching for streaming",
                        "content-type": "payload media type",
                        "x-accel-buffering": "no disables proxy buffering (SSE)",
                    }
                    print(f"    {key}: {resp.headers[key]} — {hints[key]}")

            # read raw SSE lines
            buffer: list[str] = []
            async for line in resp.aiter_lines():
                # Print raw line
                print(f"[{now()}] SSE << {line}")
                if line == "":
                    # end of event
                    event = "message"
                    data_lines: list[str] = []
                    for l in buffer:
                        if l.startswith("event:"):
                            event = l[len("event:"):].strip()
                        elif l.startswith("data:"):
                            data_lines.append(l[len("data:"):].strip())
                    data = "\n".join(data_lines)
                    buffer.clear()

                    if event == "endpoint":
                        # same-origin check
                        url_parsed = urlparse(self.url)
                        endpoint_url = urljoin(self.url, data)
                        ep_parsed = urlparse(endpoint_url)
                        if url_parsed.netloc != ep_parsed.netloc or url_parsed.scheme != ep_parsed.scheme:
                            raise ValueError("Endpoint origin does not match connection origin")
                        # start post writer
                        # start the POST writer on the main task group
                        self._tg.start_soon(self._post_writer, endpoint_url)
                    elif event == "message":
                        if data.strip():
                            msg = JSONRPCMessage.model_validate_json(data)
                            await self._read_stream_writer.send(SessionMessage(msg))
                    else:
                        # ignore other events
                        pass
                else:
                    buffer.append(line)

        await self._read_stream_writer.aclose()

    async def __aenter__(self):
        self._client = httpx.AsyncClient(follow_redirects=True)
        self._tg = await anyio.create_task_group().__aenter__()
        self._tg.start_soon(self._sse_reader)
        return self._read_stream, self._write_stream

    async def __aexit__(self, exc_type, exc, tb):
        await self._read_stream_writer.aclose()
        await self._write_stream.aclose()
        # Ensure streaming task exits (SSE is long-lived)
        self._tg.cancel_scope.cancel()
        await self._tg.__aexit__(exc_type, exc, tb)
        assert self._client is not None
        await self._client.aclose()

async def main() -> None:
    sse_url = "http://127.0.0.1:8000/sse"
    print_sep("Connect SSE")
    print(f"[{now()}] Connecting -> {sse_url}")

    # Use raw SSE client to show actual SSE lines
    async with RawSSEClient(sse_url) as (read, write):
        async with ClientSession(read, write, message_handler=message_tap) as session:
            # Initialize
            print_sep("Initialize")
            print(f"[{now()}] >> initialize")
            init = await session.initialize()
            print(f"[{now()}] << initialize.result protocol={init.protocolVersion}")

            # Discover tools
            print_sep("List Tools")
            print(f"[{now()}] >> tools/list")
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"[{now()}] << tools/list.result tools={tool_names}")

            # Stream demo to showcase SSE notifications
            print_sep("Stream Demo")
            print(f"[{now()}] >> tools/call stream_demo")

            async def on_progress(p: float, t: float | None, msg: str | None) -> None:
                print(f"[{now()}] ~~ progress callback: {p}/{t} {msg or ''}")

            stream_res = await session.call_tool(
                name="stream_demo",
                arguments={"seconds": 1.5, "steps": 4},
                progress_callback=on_progress,
            )
            if stream_res.structuredContent is not None:
                print(f"[{now()}] << stream_demo.structured {stream_res.structuredContent}")

            # Call simple calculator tool
            print_sep("Call Tool: calculator")
            print(f"[{now()}] >> tools/call calculator")
            result = await session.call_tool(
                name="calculator",
                arguments={"a": 7, "b": 4, "operation": "add"},
            )

            # Unstructured content
            if result.content:
                block = result.content[0]
                if isinstance(block, types.TextContent):
                    print(f"[{now()}] << tools/call.result text={block.text}")
            # Structured content (if provided)
            if result.structuredContent is not None:
                print(f"[{now()}] << tools/call.structured {result.structuredContent}")


if __name__ == "__main__":
    anyio.run(main)
