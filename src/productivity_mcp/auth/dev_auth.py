"""
Development mode authentication bypass.
For MVP: Uses hardcoded user ID when DISABLE_AUTH=true.
Phase 2: Extract user ID from Scalekit OAuth JWT.
"""

from productivity_mcp.config import Config
from productivity_mcp.utils.errors import AuthenticationError


def get_current_user() -> str:
    """
    Get the current authenticated user ID.

    In dev mode (DISABLE_AUTH=true), returns DEFAULT_USER_ID.
    In production, would extract from JWT token (Phase 2).

    Returns:
        User ID string

    Raises:
        AuthenticationError: If authentication fails (Phase 2)
    """
    if Config.is_dev_mode():
        return Config.DEFAULT_USER_ID

    # Phase 2: OAuth implementation
    # from fastmcp import get_access_token
    # token = get_access_token()
    # claims = getattr(token, "claims", {}) or {}
    # user_id = claims.get("sub")
    # if not user_id:
    #     raise AuthenticationError("No user ID in token")
    # return user_id

    raise AuthenticationError(
        "Authentication not configured. Set DISABLE_AUTH=true for development mode."
    )
