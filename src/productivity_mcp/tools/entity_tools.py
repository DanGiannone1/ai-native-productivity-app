"""
MCP tools for entity CRUD operations.
These tools allow Claude to create and manage productivity data (tasks, goals, habits, etc.).
"""

from typing import Any

from productivity_mcp.auth.dev_auth import get_current_user
from productivity_mcp.services import entity_service
from productivity_mcp.utils.errors import (
    EntityNotFoundError,
    EntityValidationError,
    EntityTypeNotFoundError,
)


def create_entity_tool(
    entity_type: str,
    data: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict:
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
        >>> create_entity_tool(
        ...     "task",
        ...     {
        ...         "title": "Review Q4 metrics",
        ...         "status": "in-progress",
        ...         "priority": "high",
        ...         "dueDate": "2025-12-30T17:00:00Z"
        ...     },
        ...     metadata={"createdBy": "ai-assistant", "aiContext": "From standup discussion"}
        ... )
    """
    try:
        user_id = get_current_user()

        # Create entity
        created_entity = entity_service.create_entity(
            user_id=user_id,
            entity_type=entity_type,
            data=data,
            metadata=metadata,
        )

        return {
            "success": True,
            "message": "Entity created successfully",
            "entity_id": created_entity["id"],
            "entity_type": entity_type,
            "data": created_entity["data"],
            "created_at": created_entity["createdAt"],
        }

    except EntityTypeNotFoundError as e:
        return {
            "success": False,
            "error": "Entity type not found",
            "details": str(e),
            "hint": f"Create the '{entity_type}' entity type first using create_entity_type",
        }

    except EntityValidationError as e:
        return {
            "success": False,
            "error": "Validation failed",
            "details": str(e),
            "hint": "Check that all required fields are provided and data types match the schema",
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e),
        }


def get_entity_tool(entity_id: str) -> dict:
    """
    Retrieve an entity by its ID.

    Args:
        entity_id: Entity ID (format: "entity_type:uuid")

    Returns:
        Entity data or error details

    Example:
        >>> get_entity_tool("task:abc-123-def-456")
    """
    try:
        user_id = get_current_user()

        entity = entity_service.get_entity(user_id, entity_id)

        return {
            "success": True,
            "entity_id": entity["id"],
            "entity_type": entity["entityType"],
            "data": entity["data"],
            "metadata": entity.get("metadata", {}),
            "version": entity["version"],
            "created_at": entity["createdAt"],
            "updated_at": entity["updatedAt"],
        }

    except EntityNotFoundError as e:
        return {
            "success": False,
            "error": "Entity not found",
            "details": str(e),
            "hint": "Check that the entity ID is correct and the entity hasn't been deleted",
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e),
        }


def update_entity_tool(entity_id: str, updates: dict[str, Any]) -> dict:
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
        >>> update_entity_tool(
        ...     "task:abc-123",
        ...     {"status": "done", "completedAt": "2025-12-27T15:00:00Z"}
        ... )
    """
    try:
        user_id = get_current_user()

        updated_entity = entity_service.update_entity(
            user_id=user_id,
            entity_id=entity_id,
            updates=updates,
        )

        return {
            "success": True,
            "message": "Entity updated successfully",
            "entity_id": updated_entity["id"],
            "entity_type": updated_entity["entityType"],
            "data": updated_entity["data"],
            "version": updated_entity["version"],
            "updated_at": updated_entity["updatedAt"],
        }

    except EntityNotFoundError as e:
        return {
            "success": False,
            "error": "Entity not found",
            "details": str(e),
        }

    except EntityValidationError as e:
        return {
            "success": False,
            "error": "Validation failed",
            "details": str(e),
            "hint": "Updates must conform to the entity type schema",
        }

    except EntityTypeNotFoundError as e:
        return {
            "success": False,
            "error": "Entity type schema no longer exists",
            "details": str(e),
            "hint": "The schema for this entity type may have been deleted",
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e),
        }


def list_entities_tool(
    entity_type: str,
    filters: dict[str, Any] | None = None,
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
        >>> list_entities_tool(
        ...     "task",
        ...     filters={"status": "in-progress"},
        ...     sort_by="dueDate",
        ...     limit=20
        ... )
    """
    try:
        user_id = get_current_user()

        # Cap limit at 100
        limit = min(limit, 100)

        entities = entity_service.list_entities(
            user_id=user_id,
            entity_type=entity_type,
            filters=filters,
            sort_by=sort_by,
            sort_descending=sort_descending,
            limit=limit,
        )

        # Format results
        formatted_entities = [
            {
                "entity_id": entity["id"],
                "data": entity["data"],
                "created_at": entity["createdAt"],
                "updated_at": entity["updatedAt"],
            }
            for entity in entities
        ]

        return {
            "success": True,
            "entity_type": entity_type,
            "count": len(formatted_entities),
            "entities": formatted_entities,
            "filters": filters or {},
            "sort_by": sort_by,
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Failed to list entities",
            "details": str(e),
        }


def delete_entity_tool(entity_id: str, hard_delete: bool = False) -> dict:
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
        >>> delete_entity_tool("task:abc-123")  # Soft delete
        >>> delete_entity_tool("task:abc-123", hard_delete=True)  # Permanent
    """
    try:
        user_id = get_current_user()

        entity_service.delete_entity(
            user_id=user_id,
            entity_id=entity_id,
            hard_delete=hard_delete,
        )

        delete_type = "permanently deleted" if hard_delete else "deleted"

        return {
            "success": True,
            "message": f"Entity {delete_type} successfully",
            "entity_id": entity_id,
            "hard_delete": hard_delete,
        }

    except EntityNotFoundError as e:
        return {
            "success": False,
            "error": "Entity not found",
            "details": str(e),
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e),
        }


def count_entities_tool(entity_type: str) -> dict:
    """
    Count the number of entities of a specific type.

    Args:
        entity_type: Type of entities to count

    Returns:
        Count of entities

    Example:
        >>> count_entities_tool("task")
        {"success": True, "entity_type": "task", "count": 42}
    """
    try:
        user_id = get_current_user()

        count = entity_service.count_entities(user_id, entity_type)

        return {
            "success": True,
            "entity_type": entity_type,
            "count": count,
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Failed to count entities",
            "details": str(e),
        }
