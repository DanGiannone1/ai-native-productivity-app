"""
Configuration module for productivity MCP server.
Loads and validates environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment-specific file based on ENVIRONMENT variable
env = os.getenv("ENVIRONMENT", "dev")
env_file = f".env.{env}"

if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Fallback to standard .env
    load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    # Cosmos DB
    COSMOS_HOST: str = os.getenv("COSMOS_HOST", "")
    COSMOS_KEY: str = os.getenv("COSMOS_KEY", "")
    COSMOS_DATABASE: str = os.getenv("COSMOS_DATABASE", "productivity")
    COSMOS_CONTAINER: str = os.getenv("COSMOS_CONTAINER", "productivity-data")

    # Authentication
    DISABLE_AUTH: bool = os.getenv("DISABLE_AUTH", "false").lower() == "true"
    DEFAULT_USER_ID: str = os.getenv("DEFAULT_USER_ID", "dev-user")

    # Scalekit OAuth (Phase 2)
    SCALEKIT_ENVIRONMENT_URL: str = os.getenv("SCALEKIT_ENVIRONMENT_URL", "")
    SCALEKIT_CLIENT_ID: str = os.getenv("SCALEKIT_CLIENT_ID", "")
    SCALEKIT_CLIENT_SECRET: str = os.getenv("SCALEKIT_CLIENT_SECRET", "")
    SCALEKIT_RESOURCE_ID: str = os.getenv("SCALEKIT_RESOURCE_ID", "")
    MCP_URL: str = os.getenv("MCP_URL", "")
    AUTHORIZED_M2M_CLIENTS: list[str] = os.getenv("AUTHORIZED_M2M_CLIENTS", "").split(",")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.COSMOS_HOST:
            raise ValueError("COSMOS_HOST environment variable is required")
        if not cls.COSMOS_KEY:
            raise ValueError("COSMOS_KEY environment variable is required")
        if not cls.COSMOS_DATABASE:
            raise ValueError("COSMOS_DATABASE environment variable is required")
        if not cls.COSMOS_CONTAINER:
            raise ValueError("COSMOS_CONTAINER environment variable is required")

    @classmethod
    def is_dev_mode(cls) -> bool:
        """Check if running in development mode with auth disabled."""
        return cls.DISABLE_AUTH


# Validate configuration on module import
Config.validate()
