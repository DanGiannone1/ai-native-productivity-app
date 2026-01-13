"""
Initialize Cosmos DB database and container.
Run this script to set up the infrastructure before starting the MCP server.

Usage:
    python scripts/init_cosmos.py
    OR
    .\run_local.ps1 init
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from productivity_mcp.config import Config
from productivity_mcp.cosmos_client import create_container_if_not_exists
from productivity_mcp.utils.errors import CosmosDBError


def main():
    """Initialize Cosmos DB infrastructure."""
    print("=" * 60)
    print("Initializing Cosmos DB for Productivity MCP Server")
    print("=" * 60)
    print()

    print(f"Environment: {Config.ENVIRONMENT}")
    print(f"Database: {Config.COSMOS_DATABASE}")
    print(f"Container: {Config.COSMOS_CONTAINER}")
    print(f"Host: {Config.COSMOS_HOST}")
    print()

    try:
        # Create database and container
        print("Creating database and container if not exists...")
        container = create_container_if_not_exists()

        print()
        print("=" * 60)
        print("[OK] Initialization complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run: .\\run_local.ps1 mcp")
        print("  2. Configure Claude Desktop to connect to http://localhost:8000")
        print()

    except CosmosDBError as e:
        print()
        print("=" * 60)
        print("[FAILED] Initialization failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Please check your .env file and ensure:")
        print("  - COSMOS_HOST is correct")
        print("  - COSMOS_KEY is valid")
        print("  - Cosmos account is accessible")
        sys.exit(1)

    except ValueError as e:
        print()
        print("=" * 60)
        print("[ERROR] Configuration error!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Please ensure your .env file is configured correctly.")
        print("Copy .env.example to .env and fill in the required values.")
        sys.exit(1)


if __name__ == "__main__":
    main()
