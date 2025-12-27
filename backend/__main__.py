"""
Entry point for running backend as a module.
Usage: python -m backend
"""

from backend.mcp_server import mcp

if __name__ == "__main__":
    mcp.run()
