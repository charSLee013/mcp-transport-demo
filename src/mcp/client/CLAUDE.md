# Client Layer - Model Context Protocol

**Module**: `src/mcp/client/`
**Navigation**: [Python SDK](../CLAUDE.md) → Client Layer

## Overview

The Client Layer provides the interface for applications to interact with MCP servers. This includes managing sessions, executing tools, and handling protocol communication.

## Key Components

### ClientSession (`session.py`)
- Main client interface for interacting with MCP servers
- Handles tool execution and session lifecycle management
- Provides methods for calling tools, listing resources, and handling notifications

### ClientSessionGroup (`session_group.py`)
- Manages multiple client sessions simultaneously
- Coordinates between different server connections

### Stdio Integration (`stdio/`)
- Provides standard I/O based server integration
- Handles bidirectional communication over stdio

### StdioServerParameters (`stdio.py`)
- Configuration for stdio-based server communication
- Supports both synchronous and asynchronous operation modes

## Core Interfaces

- `initialize()`: Initialize connection to server
- `call_tool()`: Execute a specific tool on the server
- `read_resource()`: Read resources from the server
- `list_tools()`: Discover available tools on the server
- `list_resources()`: List available resources

## Dependencies

- `anyio`: Asynchronous I/O framework
- `httpx`: HTTP client library
- `pydantic`: Data validation and settings management

## Testing Strategy

Located in `tests/client/`:
- Unit tests for session management
- Integration tests for tool execution
- Protocol compliance verification

## Usage Patterns

```python
from mcp import ClientSession, StdioServerParameters
from mcp.types import CallToolRequest

# Initialize client session
async with ClientSession.create(
    server_params=StdioServerParameters(command=["my-server"])
) as session:
    result = await session.call_tool(
        CallToolRequest(name="calculator", arguments={"operation": "add", "a": 5, "b": 3
    )
```