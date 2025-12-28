"""
MCP tools for schema management.
These tools allow Claude to create and manage entity type schemas dynamically.
"""

from typing import Any

from productivity_mcp.auth.dev_auth import get_current_user
from productivity_mcp.services import schema_service
from productivity_mcp.utils.errors import SchemaNotFoundError, SchemaValidationError, EntityTypeNotFoundError


def create_entity_type_tool(
    entity_type_name: str,
    schema_definition: dict[str, Any],
    display_config: dict[str, Any] | None = None,
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
        >>> create_entity_type_tool(
        ...     "task",
        ...     {
        ...         "title": {"type": "string", "required": True},
        ...         "status": {
        ...             "type": "enum",
        ...             "enum_values": ["todo", "in-progress", "done"],
        ...             "default": "todo"
        ...         },
        ...         "priority": {"type": "enum", "enum_values": ["low", "medium", "high"]},
        ...         "dueDate": {"type": "datetime"}
        ...     },
        ...     {"icon": "task-icon", "color": "#4A90E2"}
        ... )
    """
    try:
        user_id = get_current_user()

        # Create entity type
        updated_schema = schema_service.create_entity_type(
            user_id=user_id,
            entity_type_name=entity_type_name,
            schema_definition=schema_definition,
            display_config=display_config,
        )

        entity_type_schema = updated_schema.entity_types[entity_type_name]

        return {
            "success": True,
            "message": f"Entity type '{entity_type_name}' created successfully",
            "entity_type": entity_type_name,
            "schema": {
                field_name: {
                    "type": field_def.type,
                    "required": field_def.required,
                    "default": field_def.default,
                    "enum_values": field_def.enum_values,
                }
                for field_name, field_def in entity_type_schema.schema.items()
            },
            "version": entity_type_schema.version,
            "field_count": len(entity_type_schema.schema),
        }

    except SchemaValidationError as e:
        return {
            "success": False,
            "error": "Schema validation failed",
            "details": str(e),
            "hint": "Check that all enum fields have enum_values and field types are valid",
        }

    except ValueError as e:
        return {
            "success": False,
            "error": "Entity type already exists",
            "details": str(e),
            "hint": f"Use update_entity_type to modify existing '{entity_type_name}' schema",
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e),
        }


def get_user_schema_tool() -> dict:
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
                    "required_fields": ["title"]
                },
                ...
            }
        }
    """
    try:
        user_id = get_current_user()

        user_schema = schema_service.get_user_schema(user_id)

        # Format schema for readability
        formatted_schemas = {}
        for entity_type_name, entity_schema in user_schema.entity_types.items():
            formatted_schemas[entity_type_name] = {
                "version": entity_schema.version,
                "fields": entity_schema.get_field_names(),
                "required_fields": entity_schema.get_required_fields(),
                "schema": {
                    field_name: {
                        "type": field_def.type,
                        "required": field_def.required,
                        "default": field_def.default,
                        "enum_values": field_def.enum_values,
                    }
                    for field_name, field_def in entity_schema.schema.items()
                },
                "display_config": (
                    entity_schema.display_config.model_dump() if entity_schema.display_config else None
                ),
            }

        return {
            "success": True,
            "entity_types": list(user_schema.entity_types.keys()),
            "count": len(user_schema.entity_types),
            "schemas": formatted_schemas,
            "schema_version": user_schema.version,
        }

    except SchemaNotFoundError:
        return {
            "success": True,
            "entity_types": [],
            "count": 0,
            "schemas": {},
            "message": "No schema found. Create your first entity type to get started!",
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Failed to retrieve schema",
            "details": str(e),
        }


def update_entity_type_tool(
    entity_type_name: str,
    schema_updates: dict[str, Any] | None = None,
    display_config: dict[str, Any] | None = None,
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
        >>> update_entity_type_tool(
        ...     "task",
        ...     schema_updates={"tags": {"type": "array"}},
        ...     display_config={"sort_by": "dueDate"}
        ... )
    """
    try:
        user_id = get_current_user()

        updated_schema = schema_service.update_entity_type(
            user_id=user_id,
            entity_type_name=entity_type_name,
            schema_updates=schema_updates,
            display_config=display_config,
        )

        entity_schema = updated_schema.entity_types[entity_type_name]

        return {
            "success": True,
            "message": f"Entity type '{entity_type_name}' updated successfully",
            "entity_type": entity_type_name,
            "version": entity_schema.version,
            "field_count": len(entity_schema.schema),
        }

    except SchemaNotFoundError:
        return {
            "success": False,
            "error": "Schema not found",
            "hint": "User has no schema document. Create an entity type first.",
        }

    except EntityTypeNotFoundError as e:
        return {
            "success": False,
            "error": "Entity type not found",
            "details": str(e),
            "hint": f"Entity type '{entity_type_name}' does not exist. Use create_entity_type instead.",
        }

    except SchemaValidationError as e:
        return {
            "success": False,
            "error": "Schema validation failed",
            "details": str(e),
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e),
        }


def delete_entity_type_tool(entity_type_name: str, confirm: bool = False) -> dict:
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
    if not confirm:
        return {
            "success": False,
            "error": "Deletion not confirmed",
            "message": "Set confirm=True to delete this entity type",
            "warning": "Deleting the schema does not delete existing entities of this type",
        }

    try:
        user_id = get_current_user()

        # TODO: Check for existing entities (Phase 2)
        # entity_count = entity_service.count_entities(user_id, entity_type_name)
        # if entity_count > 0:
        #     return {
        #         "success": False,
        #         "error": "Cannot delete entity type with existing entities",
        #         "entity_count": entity_count,
        #         "hint": "Delete all entities of this type first"
        #     }

        updated_schema = schema_service.delete_entity_type(
            user_id=user_id,
            entity_type_name=entity_type_name,
        )

        return {
            "success": True,
            "message": f"Entity type '{entity_type_name}' deleted successfully",
            "remaining_types": list(updated_schema.entity_types.keys()),
        }

    except SchemaNotFoundError:
        return {
            "success": False,
            "error": "Schema not found",
            "hint": "User has no schema document",
        }

    except EntityTypeNotFoundError as e:
        return {
            "success": False,
            "error": "Entity type not found",
            "details": str(e),
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e),
        }
