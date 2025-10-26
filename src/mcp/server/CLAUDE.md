# Server Layer - Model Context Protocol

**Module**: `src/mcp/server/`
**Navigation**: [Python SDK](../CLAUDE.md) → Server Layer

## Overview

The Server Layer implements the MCP protocol for servers. This includes handling client requests, managing resources, and providing tool implementations.

## Key Components

### FastMCP Framework (`fastmcp/`)
- High-level framework with decorator-based tool definitions
- Tools, Resources, and Prompts management
- Authentication and middleware support

### FastMCP Submodules
- **Tools** (`fastmcp/tools/`): Functionality exposed to clients
- **Resources** (`fastmcp/resources/`): Data sources accessible to clients
- **Prompts** (`fastmcp/prompts/`): Reusable prompt templates
- **Utilities** (`fastmcp/utilities/`): Internal helper functions

### Low-Level Server (`lowlevel/`)
- Core protocol implementation
- Message handling and session management

### Auth Middleware (`auth/`)
- Authentication and authorization handlers
- Middleware chain for request processing

### Session Management (`session.py`)
- Manage server sessions and client connections
- Handle initialization and capability negotiation

## Protocol Implementation

The Server Layer implements the complete MCP protocol:

1. **Initialization**: Server capabilities and client requirements
2. **Tool Execution**: Call and execute registered tools
3. **Resource Management**: Access and update resources
4. **Notifications**: Send and receive server notifications

## Dependencies

- `starlette`: ASGI web framework
- `uvicorn`: ASGI server
- `pydantic-settings**: Settings management

## Key Features

- Protocol compliant request/response handling
- Extensible middleware system
- Authentication and authorization support
- Session lifecycle management

## Testing Strategy

Located in `tests/server/`:
- Unit tests for low-level protocol
- Integration tests for FastMCP framework
- Authentication middleware tests