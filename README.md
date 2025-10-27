# MCP 工具演示 / MCP Tool Showcase

> Forked from [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk). 这个仓库聚焦于演示 Model Context Protocol（MCP）工具在不同传输层上的实际运行效果，而不是原库的全量 SDK 发行版。

## 项目背景 Background

- 保留了上游 MIT 许可的核心实现，并在 [`examples/`](examples) 与 [`scripts/`](scripts) 下补充了可直接运行的演示。
- 重点展示两个常见传输：服务器推送事件（SSE）与 Streamable HTTP。
- 提醒：任何基于本仓库的再分发或修改都必须继续遵循 [`LICENSE`](LICENSE) 中的 MIT 许可条款。

## 环境准备 Setup

1. Clone 仓库 / Clone this repo locally.
2. 使用 [uv](https://docs.astral.sh/uv/) 安装依赖（默认会创建 `.venv/`）
   ```bash
   uv sync --frozen --all-extras --dev
   ```
3. 确保 8000 端口空闲；两个演示脚本都会在本地 `127.0.0.1:8000` 启动服务器。

## 演示脚本 Demo Scripts

### SSE 传输 / SSE Transport

```bash
bash scripts/run_sse_demo.sh
```

- 脚本会自动终止占用端口的旧进程，启动 `Streamable Progress Demo` 对应的 SSE 服务器，并运行客户端。
- 服务器日志输出到 `/tmp/sse_server.log`，客户端控制台输出（包括原始 SSE 帧与 JSON-RPC 序列）写入 `/tmp/sse_client.log`。
- 终端会看到形如 `[run] starting server -> ...`、`[run] waiting for server to be ready` 的状态提示；客户端日志中会出现 `SSE << event: message`、`<< tools/list.result ...` 等行展示实时通信。

### Streamable HTTP 传输 / Streamable HTTP Transport

```bash
bash scripts/run_streamable_http_demo.sh
```

- 展示新的 Streamable HTTP 传输：客户端在同一 TCP 通道里混合使用 `POST /mcp`、`GET /mcp` 和 `DELETE /mcp`。
- 日志路径：服务器 `/tmp/streamable_http_server.log`，客户端 `/tmp/streamable_http_client.log`。
- 控制台同样会输出 `[run] running client -> ...`、`[run] client finished; stopping server` 等步骤说明，而客户端日志里可观察到 `>>> REQUEST POST http://127.0.0.1:8000/mcp`、`<< initialize.result protocol=...`、`~~ progress callback: ...` 等详细记录。

## 日志与排错 Logs & Troubleshooting

- 若脚本无法找到 `.venv/bin/python`，请确认已执行 `uv sync`；首次运行推荐：

  ```bash
  uv sync --frozen --all-extras --dev
  uv pip install -e .
  ```

  这样可在 `.venv/` 中注册项目自身的包元数据，避免运行时找不到 `mcp` 发行版。
- 如需要查看实时输出，可在运行脚本后执行 `tail -f /tmp/sse_client.log` 或 `tail -f /tmp/streamable_http_client.log`。
- 两个演示均使用 `FastMCP`，具体实现位于：
  - SSE 服务端：`examples/snippets/servers/sse_progress_demo.py`
  - Streamable HTTP 服务端：`examples/snippets/servers/streamable_progress_demo.py`
  - 客户端示例：`examples/snippets/clients/sse_progress_client.py` / `examples/snippets/clients/streamable_progress_client.py`

## 许可 License

本仓库继续沿用 MIT 许可证；请参阅 [`LICENSE`](LICENSE) 了解完整条款。
This fork remains MIT-licensed. Refer to [`LICENSE`](LICENSE) for details.
