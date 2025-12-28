"""
Schema service for managing user entity type definitions.
Handles CRUD operations on schema documents in Cosmos DB.
"""

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from productivity_mcp.cosmos_client import read_item, upsert_item
from productivity_mcp.schema.models import UserSchemaDocument, DisplayConfig, EntityTypeSchema
from productivity_mcp.schema.validator import validate_schema_definition
from productivity_mcp.utils.errors import SchemaNotFoundError, SchemaValidationError, EntityTypeNotFoundError


def get_user_schema(user_id: str) -> UserSchemaDocument:
    """
    Retrieve the schema document for a user.

    Args:
        user_id: User ID

    Returns:
        UserSchemaDocument with all entity type definitions

    Raises:
        SchemaNotFoundError: If user has no schema document
    """
    schema_id = f"schema:{user_id}"

    try:
        schema_doc = read_item(schema_id, partition_key=user_id)
        return UserSchemaDocument(**schema_doc)

    except CosmosResourceNotFoundError:
        raise SchemaNotFoundError(f"No schema found for user '{user_id}'")


def get_or_create_user_schema(user_id: str) -> UserSchemaDocument:
    """
    Get existing schema or create a new empty one.

    Args:
        user_id: User ID

    Returns:
        UserSchemaDocument (existing or newly created)
    """
    try:
        return get_user_schema(user_id)
    except SchemaNotFoundError:
        # Create new empty schema
        new_schema = UserSchemaDocument.create_for_user(user_id)
        saved_schema = upsert_item(new_schema.model_dump(by_alias=True))
        return UserSchemaDocument(**saved_schema)


def create_entity_type(
    user_id: str,
    entity_type_name: str,
    schema_definition: dict[str, dict],
    display_config: dict | None = None,
) -> UserSchemaDocument:
    """
    Create a new entity type in the user's schema.

    Args:
        user_id: User ID
        entity_type_name: Name of entity type (e.g., "task", "goal")
        schema_definition: Field definitions
        display_config: Optional UI configuration

    Returns:
        Updated UserSchemaDocument

    Raises:
        SchemaValidationError: If schema definition is invalid
        ValueError: If entity type already exists

    Example:
        >>> create_entity_type(
        ...     "user123",
        ...     "task",
        ...     {
        ...         "title": {"type": "string", "required": True},
        ...         "status": {"type": "enum", "enum_values": ["todo", "done"], "default": "todo"}
        ...     }
        ... )
    """
    # Validate schema definition
    validated_schema = validate_schema_definition(schema_definition)

    # Parse display config if provided
    parsed_display_config = None
    if display_config:
        try:
            parsed_display_config = DisplayConfig(**display_config)
        except Exception as e:
            raise SchemaValidationError(f"Invalid display config: {str(e)}")

    # Get or create user schema
    user_schema = get_or_create_user_schema(user_id)

    # Add entity type
    try:
        user_schema.add_entity_type(
            entity_type_name=entity_type_name,
            schema=validated_schema,
            display_config=parsed_display_config,
        )
    except ValueError:
        # Re-raise as-is (entity type already exists)
        raise

    # Save to Cosmos
    saved_doc = upsert_item(user_schema.model_dump(by_alias=True, mode='json'))
    return UserSchemaDocument(**saved_doc)


def update_entity_type(
    user_id: str,
    entity_type_name: str,
    schema_updates: dict[str, dict] | None = None,
    display_config: dict | None = None,
) -> UserSchemaDocument:
    """
    Update an existing entity type schema.

    Args:
        user_id: User ID
        entity_type_name: Name of entity type
        schema_updates: Updated field definitions (merged with existing)
        display_config: Updated display config

    Returns:
        Updated UserSchemaDocument

    Raises:
        SchemaNotFoundError: If user has no schema
        EntityTypeNotFoundError: If entity type doesn't exist
        SchemaValidationError: If updates are invalid

    Example:
        >>> update_entity_type(
        ...     "user123",
        ...     "task",
        ...     schema_updates={"priority": {"type": "enum", "enum_values": ["low", "high"]}}
        ... )
    """
    # Get existing schema
    user_schema = get_user_schema(user_id)

    # Validate schema updates if provided
    validated_updates = None
    if schema_updates:
        validated_updates = validate_schema_definition(schema_updates)

    # Parse display config if provided
    parsed_display_config = None
    if display_config:
        try:
            parsed_display_config = DisplayConfig(**display_config)
        except Exception as e:
            raise SchemaValidationError(f"Invalid display config: {str(e)}")

    # Update entity type
    try:
        user_schema.update_entity_type(
            entity_type_name=entity_type_name,
            schema_updates=validated_updates,
            display_config=parsed_display_config,
        )
    except ValueError as e:
        raise EntityTypeNotFoundError(str(e))

    # Save to Cosmos
    saved_doc = upsert_item(user_schema.model_dump(by_alias=True, mode='json'))
    return UserSchemaDocument(**saved_doc)


def delete_entity_type(user_id: str, entity_type_name: str) -> UserSchemaDocument:
    """
    Delete an entity type from the user's schema.

    WARNING: This does NOT delete existing entities of this type.
    The caller should check for existing entities before deleting.

    Args:
        user_id: User ID
        entity_type_name: Name of entity type to delete

    Returns:
        Updated UserSchemaDocument

    Raises:
        SchemaNotFoundError: If user has no schema
        EntityTypeNotFoundError: If entity type doesn't exist
    """
    # Get existing schema
    user_schema = get_user_schema(user_id)

    # Remove entity type
    try:
        user_schema.remove_entity_type(entity_type_name)
    except ValueError as e:
        raise EntityTypeNotFoundError(str(e))

    # Save to Cosmos
    saved_doc = upsert_item(user_schema.model_dump(by_alias=True, mode='json'))
    return UserSchemaDocument(**saved_doc)


def entity_type_exists(user_id: str, entity_type_name: str) -> bool:
    """
    Check if an entity type exists in the user's schema.

    Args:
        user_id: User ID
        entity_type_name: Name of entity type

    Returns:
        True if entity type exists, False otherwise
    """
    try:
        user_schema = get_user_schema(user_id)
        return user_schema.has_entity_type(entity_type_name)
    except SchemaNotFoundError:
        return False


def get_entity_type_schema(user_id: str, entity_type_name: str) -> EntityTypeSchema:
    """
    Get the schema for a specific entity type.

    Args:
        user_id: User ID
        entity_type_name: Name of entity type

    Returns:
        EntityTypeSchema

    Raises:
        SchemaNotFoundError: If user has no schema
        EntityTypeNotFoundError: If entity type doesn't exist
    """
    user_schema = get_user_schema(user_id)

    try:
        return user_schema.get_entity_type(entity_type_name)
    except ValueError as e:
        raise EntityTypeNotFoundError(str(e))


def count_entity_types(user_id: str) -> int:
    """
    Count the number of entity types defined for a user.

    Args:
        user_id: User ID

    Returns:
        Number of entity types
    """
    try:
        user_schema = get_user_schema(user_id)
        return len(user_schema.entity_types)
    except SchemaNotFoundError:
        return 0
