"""
Entry point for running productivity_mcp as a module.
Usage: python -m productivity_mcp
"""

from productivity_mcp.mcp_server import mcp

if __name__ == "__main__":
    mcp.run()
