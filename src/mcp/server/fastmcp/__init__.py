"""FastMCP - A more ergonomic interface for MCP servers."""

from importlib.metadata import PackageNotFoundError, version

from mcp.types import Icon

from .server import Context, FastMCP
from .utilities.types import Audio, Image

try:
    __version__ = version("mcp")
except PackageNotFoundError:
    # Fallback for editable/local installs that lack package metadata.
    __version__ = "0.0.0+local"
__all__ = ["FastMCP", "Context", "Image", "Audio", "Icon"]
