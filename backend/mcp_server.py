"""
FastMCP server for the productivity system.
Entry point for the MCP server that exposes schema and entity management tools.

Run with: python -m backend.mcp_server
OR: .\run_local.ps1 mcp
"""

import logging
from fastmcp import FastMCP

from backend.config import Config
from backend.tools.schema_tools import (
    create_entity_type_tool,
    get_user_schema_tool,
    update_entity_type_tool,
    delete_entity_type_tool,
)
from backend.tools.entity_tools import (
    create_entity_tool,
    get_entity_tool,
    update_entity_tool,
    list_entities_tool,
    delete_entity_tool,
    count_entities_tool,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "Productivity MCP Server",
    dependencies=[],
)

logger.info(f"Initializing Productivity MCP Server (Environment: {Config.ENVIRONMENT})")
logger.info(f"Auth mode: {'DEV (disabled)' if Config.is_dev_mode() else 'PRODUCTION (OAuth)'}")
logger.info(f"Database: {Config.COSMOS_DATABASE}")
logger.info(f"Container: {Config.COSMOS_CONTAINER}")


# ============================================================================
# Schema Management Tools
# ============================================================================


@mcp.tool()
def create_entity_type(
    entity_type_name: str,
    schema_definition: dict,
    display_config: dict | None = None,
) -> dict:
    """
    Create a new entity type for the user's productivity system.

    This tool allows Claude to dynamically define new entity types based on the
    user's mental model. For example, if a user wants to track "habits", "goals",
    or custom types like "learning-resources", Claude can create appropriate schemas.

    Args:
        entity_type_name: Name of the entity type (e.g., "task", "goal", "habit").
                         Should be lowercase, no spaces (use hyphens or underscores).
        schema_definition: Field definitions for this entity type. Each field has:
                          - type: One of "string", "number", "boolean", "enum", "datetime", "array", "object"
                          - required: Whether the field is required (default: false)
                          - default: Default value if not provided (optional)
                          - enum_values: For enum type, list of allowed values (required for enums)
        display_config: Optional UI hints (icon, color, default_view, sort_by, group_by)

    Returns:
        Success response with created schema or error details

    Example:
        create_entity_type(
            "task",
            {
                "title": {"type": "string", "required": True},
                "status": {
                    "type": "enum",
                    "enum_values": ["todo", "in-progress", "done"],
                    "default": "todo"
                },
                "priority": {"type": "enum", "enum_values": ["low", "medium", "high"]},
                "dueDate": {"type": "datetime"}
            },
            {"icon": "task-icon", "color": "#4A90E2"}
        )
    """
    logger.info(f"Creating entity type: {entity_type_name}")
    result = create_entity_type_tool(entity_type_name, schema_definition, display_config)

    if result.get("success"):
        logger.info(f"✓ Entity type '{entity_type_name}' created with {result.get('field_count')} fields")
    else:
        logger.error(f"✗ Failed to create entity type '{entity_type_name}': {result.get('error')}")

    return result


@mcp.tool()
def get_user_schema() -> dict:
    """
    Get all entity type definitions for the current user.

    This returns the complete schema showing all entity types the user has defined.
    Useful for understanding what types exist before creating entities.

    Returns:
        User's complete schema or error details

    Example response:
        {
            "success": True,
            "entity_types": ["task", "goal", "habit"],
            "count": 3,
            "schemas": {
                "task": {
                    "version": 1,
                    "fields": ["title", "status", "priority", "dueDate"],
                    "required_fields": ["title"],
                    "schema": {...}
                },
                ...
            }
        }
    """
    logger.info("Retrieving user schema")
    result = get_user_schema_tool()

    if result.get("success"):
        logger.info(f"✓ Retrieved schema with {result.get('count')} entity types")
    else:
        logger.error(f"✗ Failed to retrieve schema: {result.get('error')}")

    return result


@mcp.tool()
def update_entity_type(
    entity_type_name: str,
    schema_updates: dict | None = None,
    display_config: dict | None = None,
) -> dict:
    """
    Update an existing entity type schema.

    This allows adding new fields or updating display configuration for an existing
    entity type. Schema updates are merged with the existing schema.

    Args:
        entity_type_name: Name of the entity type to update
        schema_updates: New or updated field definitions (merged with existing)
        display_config: Updated display configuration

    Returns:
        Success response or error details

    Example:
        update_entity_type(
            "task",
            schema_updates={"tags": {"type": "array"}},
            display_config={"sort_by": "dueDate"}
        )
    """
    logger.info(f"Updating entity type: {entity_type_name}")
    result = update_entity_type_tool(entity_type_name, schema_updates, display_config)

    if result.get("success"):
        logger.info(f"✓ Entity type '{entity_type_name}' updated to version {result.get('version')}")
    else:
        logger.error(f"✗ Failed to update entity type '{entity_type_name}': {result.get('error')}")

    return result


@mcp.tool()
def delete_entity_type(entity_type_name: str, confirm: bool = False) -> dict:
    """
    Delete an entity type from the user's schema.

    WARNING: This does not delete existing entities of this type. You should
    check for existing entities before deleting the schema.

    Args:
        entity_type_name: Name of the entity type to delete
        confirm: Must be True to actually delete (safety check)

    Returns:
        Success response or error details
    """
    logger.info(f"Deleting entity type: {entity_type_name} (confirm={confirm})")
    result = delete_entity_type_tool(entity_type_name, confirm)

    if result.get("success"):
        logger.info(f"✓ Entity type '{entity_type_name}' deleted")
    else:
        logger.warning(f"✗ Failed to delete entity type '{entity_type_name}': {result.get('error')}")

    return result


# ============================================================================
# Entity CRUD Tools
# ============================================================================


@mcp.tool()
def create_entity(entity_type: str, data: dict, metadata: dict | None = None) -> dict:
    """
    Create a new entity instance (task, goal, habit, etc.).

    This tool creates a new productivity item based on the entity type schema.
    The data must conform to the schema defined for this entity type.

    Args:
        entity_type: Type of entity to create (e.g., "task", "goal", "habit")
        data: Entity data matching the schema for this type
        metadata: Optional metadata (createdBy, aiContext, source, etc.)

    Returns:
        Success response with created entity or error details

    Example:
        create_entity(
            "task",
            {
                "title": "Review Q4 metrics",
                "status": "in-progress",
                "priority": "high",
                "dueDate": "2025-12-30T17:00:00Z"
            },
            metadata={"createdBy": "ai-assistant", "aiContext": "From standup discussion"}
        )
    """
    logger.info(f"Creating {entity_type} entity")
    result = create_entity_tool(entity_type, data, metadata)

    if result.get("success"):
        logger.info(f"✓ Entity created: {result.get('entity_id')}")
    else:
        logger.error(f"✗ Failed to create entity: {result.get('error')}")

    return result


@mcp.tool()
def get_entity(entity_id: str) -> dict:
    """
    Retrieve an entity by its ID.

    Args:
        entity_id: Entity ID (format: "entity_type:uuid")

    Returns:
        Entity data or error details

    Example:
        get_entity("task:abc-123-def-456")
    """
    logger.info(f"Retrieving entity: {entity_id}")
    result = get_entity_tool(entity_id)

    if result.get("success"):
        logger.info(f"✓ Entity retrieved: {entity_id}")
    else:
        logger.error(f"✗ Failed to retrieve entity: {result.get('error')}")

    return result


@mcp.tool()
def update_entity(entity_id: str, updates: dict) -> dict:
    """
    Update an existing entity.

    This performs a partial update - only the fields in `updates` are modified.
    Other fields remain unchanged.

    Args:
        entity_id: Entity ID
        updates: Fields to update (partial data)

    Returns:
        Success response with updated entity or error details

    Example:
        update_entity(
            "task:abc-123",
            {"status": "done", "completedAt": "2025-12-27T15:00:00Z"}
        )
    """
    logger.info(f"Updating entity: {entity_id}")
    result = update_entity_tool(entity_id, updates)

    if result.get("success"):
        logger.info(f"✓ Entity updated: {entity_id} (version {result.get('version')})")
    else:
        logger.error(f"✗ Failed to update entity: {result.get('error')}")

    return result


@mcp.tool()
def list_entities(
    entity_type: str,
    filters: dict | None = None,
    sort_by: str | None = None,
    sort_descending: bool = False,
    limit: int = 50,
) -> dict:
    """
    List entities of a specific type with optional filtering and sorting.

    Args:
        entity_type: Type of entities to list (e.g., "task", "goal")
        filters: Optional filters on data fields (e.g., {"status": "todo"})
        sort_by: Optional field name to sort by (must exist in entity data)
        sort_descending: Sort in descending order (default: ascending)
        limit: Maximum number of results (default: 50, max: 100)

    Returns:
        List of entities or error details

    Example:
        list_entities(
            "task",
            filters={"status": "in-progress"},
            sort_by="dueDate",
            limit=20
        )
    """
    logger.info(f"Listing {entity_type} entities (limit={limit})")
    result = list_entities_tool(entity_type, filters, sort_by, sort_descending, limit)

    if result.get("success"):
        logger.info(f"✓ Found {result.get('count')} {entity_type} entities")
    else:
        logger.error(f"✗ Failed to list entities: {result.get('error')}")

    return result


@mcp.tool()
def delete_entity(entity_id: str, hard_delete: bool = False) -> dict:
    """
    Delete an entity.

    By default, performs a soft delete (entity is marked deleted but not removed).
    Hard delete permanently removes the entity from the database.

    Args:
        entity_id: Entity ID to delete
        hard_delete: If True, permanently delete. If False, soft delete (default).

    Returns:
        Success response or error details

    Example:
        delete_entity("task:abc-123")  # Soft delete
        delete_entity("task:abc-123", hard_delete=True)  # Permanent
    """
    logger.info(f"Deleting entity: {entity_id} (hard={hard_delete})")
    result = delete_entity_tool(entity_id, hard_delete)

    if result.get("success"):
        logger.info(f"✓ Entity deleted: {entity_id}")
    else:
        logger.error(f"✗ Failed to delete entity: {result.get('error')}")

    return result


@mcp.tool()
def count_entities(entity_type: str) -> dict:
    """
    Count the number of entities of a specific type.

    Args:
        entity_type: Type of entities to count

    Returns:
        Count of entities

    Example:
        count_entities("task")
    """
    logger.info(f"Counting {entity_type} entities")
    result = count_entities_tool(entity_type)

    if result.get("success"):
        logger.info(f"✓ Found {result.get('count')} {entity_type} entities")
    else:
        logger.error(f"✗ Failed to count entities: {result.get('error')}")

    return result


# ============================================================================
# Server Startup Info
# ============================================================================

logger.info("=" * 60)
logger.info("Productivity MCP Server Ready")
logger.info("=" * 60)
logger.info("")
logger.info("Available tools:")
logger.info("  Schema Management:")
logger.info("    - create_entity_type: Define new entity types")
logger.info("    - get_user_schema: View all entity type definitions")
logger.info("    - update_entity_type: Modify existing schemas")
logger.info("    - delete_entity_type: Remove entity types")
logger.info("  Entity Management:")
logger.info("    - create_entity: Create new entities (tasks, goals, etc.)")
logger.info("    - get_entity: Retrieve entity by ID")
logger.info("    - update_entity: Modify existing entities")
logger.info("    - list_entities: List entities with filtering/sorting")
logger.info("    - delete_entity: Delete entities (soft or hard)")
logger.info("    - count_entities: Count entities of a type")
logger.info("")
logger.info("Start with: uvicorn backend.mcp_server:app --host 0.0.0.0 --port 8000")
logger.info("=" * 60)

# ============================================================================
# ASGI App Export for Uvicorn
# ============================================================================

# Export the ASGI app (SSE transport for MCP protocol)
app = mcp.sse_app()

# Direct run support
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
