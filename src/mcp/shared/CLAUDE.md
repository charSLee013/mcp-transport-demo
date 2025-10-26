# Shared Infrastructure - Model Context Protocol

**Module**: `src/mcp/shared/`
**Navigation**: [Python SDK](../CLAUDE.md) → Shared Infrastructure

## Overview

The Shared Infrastructure module contains cross-cutting concerns that are used by both client and server layers.

## Key Components

### Types & Models (`types.py`)
- Protocol message types and data models
- JSON-RPC request/response structures
- Error handling and validation models

### Exceptions (`exceptions.py`)
- Error classes and exception hierarchy for the entire SDK

## Core Components

### Types (`types.py`)
- Message structures for MCP protocol
- Includes: `CallToolRequest`, `ClientCapabilities`, `JsonRPCError`, etc.
- Pydantic models for type-safe data validation

## Key Data Models

- **Session Management**: Client and server session types
- **Tool & Resource Management**: Structures for tools and resources
- **Protocol Messages**: Complete MCP protocol message definitions

### Protocol Support

- **JSON-RPC**: Request and response message formats
- **Capabilities**: Server and client capability definitions
- **Notifications**: Event notification structures

## Usage Patterns

Shared types are imported by both client and server implementations:

```python
from mcp.types import (
    CallToolRequest,
    ClientCapabilities,
    ServerCapabilities
)

## Error Hierarchy

- **McpError**: Base exception for all MCP-related errors
- **Protocol Errors**: JSON-RPC and MCP protocol exceptions

## Dependencies

- `pydantic`: Data validation and serialization
- Standard Python typing support