from mcp.server.fastmcp import FastMCP

# Create the MCP server with FastMCP framework
mcp = FastMCP("Simple Calculator Server")


@mcp.tool()
async def add_numbers(a: float, b: float) -> str:
    """Add two numbers together."""
    return f"结果: {a} + {b} = {a + b}"


@mcp.tool()
async def subtract_numbers(a: float, b: float) -> str:
    """Subtract second number from first number."""
    return f"结果: {a} - {b} = {a - b}"


if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run("stdio")