"""
Entity service for managing productivity data (tasks, goals, habits, etc.).
Handles CRUD operations on entity documents in Cosmos DB.
"""

from datetime import datetime
from uuid import uuid4
from typing import Any

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from productivity_mcp.cosmos_client import create_item, read_item, upsert_item, delete_item, query_items
from productivity_mcp.schema.validator import validate_and_apply_defaults
from productivity_mcp.services import schema_service
from productivity_mcp.utils.errors import (
    EntityNotFoundError,
    EntityTypeNotFoundError,
)


def create_entity(
    user_id: str,
    entity_type: str,
    data: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict:
    """
    Create a new entity instance.

    Args:
        user_id: User ID
        entity_type: Type of entity (must exist in user's schema)
        data: Entity data (will be validated against schema)
        metadata: Optional metadata (createdBy, aiContext, etc.)

    Returns:
        Created entity document with generated ID and timestamps

    Raises:
        EntityTypeNotFoundError: If entity type doesn't exist in schema
        EntityValidationError: If data doesn't conform to schema

    Example:
        >>> create_entity(
        ...     "user123",
        ...     "task",
        ...     {"title": "Review Q4 metrics", "status": "todo", "priority": "high"}
        ... )
    """
    # Get entity type schema
    try:
        entity_schema = schema_service.get_entity_type_schema(user_id, entity_type)
    except Exception as e:
        raise EntityTypeNotFoundError(f"Entity type '{entity_type}' not found in schema") from e

    # Validate and apply defaults
    validated_data = validate_and_apply_defaults(data, entity_schema)

    # Generate entity ID
    entity_id = f"{entity_type}:{uuid4()}"

    # Create entity document
    now = datetime.utcnow().isoformat() + "Z"
    entity_doc = {
        "id": entity_id,
        "docType": "entity",
        "userId": user_id,
        "entityType": entity_type,
        "version": 1,
        "data": validated_data,
        "metadata": metadata or {},
        "isDeleted": False,
        "createdAt": now,
        "updatedAt": now,
    }

    # Save to Cosmos
    created_doc = create_item(entity_doc)
    return created_doc


def get_entity(user_id: str, entity_id: str) -> dict:
    """
    Retrieve an entity by ID.

    Args:
        user_id: User ID (partition key)
        entity_id: Entity ID

    Returns:
        Entity document

    Raises:
        EntityNotFoundError: If entity doesn't exist
    """
    try:
        entity_doc = read_item(entity_id, partition_key=user_id)

        # Check if soft deleted
        if entity_doc.get("isDeleted", False):
            raise EntityNotFoundError(f"Entity '{entity_id}' has been deleted")

        return entity_doc

    except CosmosResourceNotFoundError:
        raise EntityNotFoundError(f"Entity '{entity_id}' not found")


def update_entity(
    user_id: str,
    entity_id: str,
    updates: dict[str, Any],
) -> dict:
    """
    Update an existing entity.

    Args:
        user_id: User ID (partition key)
        entity_id: Entity ID
        updates: Fields to update (partial update, merged with existing data)

    Returns:
        Updated entity document

    Raises:
        EntityNotFoundError: If entity doesn't exist
        EntityValidationError: If updates don't conform to schema
        EntityTypeNotFoundError: If entity type no longer exists in schema

    Example:
        >>> update_entity("user123", "task:abc-123", {"status": "done"})
    """
    # Get existing entity
    entity_doc = get_entity(user_id, entity_id)

    entity_type = entity_doc["entityType"]
    current_data = entity_doc["data"]

    # Get entity type schema
    try:
        entity_schema = schema_service.get_entity_type_schema(user_id, entity_type)
    except Exception as e:
        raise EntityTypeNotFoundError(
            f"Entity type '{entity_type}' no longer exists in schema"
        ) from e

    # Merge updates with existing data
    updated_data = {**current_data, **updates}

    # Validate merged data
    validated_data = validate_and_apply_defaults(updated_data, entity_schema)

    # Update document
    entity_doc["data"] = validated_data
    entity_doc["version"] += 1
    entity_doc["updatedAt"] = datetime.utcnow().isoformat() + "Z"

    # Save to Cosmos
    updated_doc = upsert_item(entity_doc)
    return updated_doc


def delete_entity(user_id: str, entity_id: str, hard_delete: bool = False) -> None:
    """
    Delete an entity.

    By default, performs soft delete (sets isDeleted=True).
    Hard delete permanently removes the document.

    Args:
        user_id: User ID (partition key)
        entity_id: Entity ID
        hard_delete: If True, permanently delete. If False, soft delete (default).

    Raises:
        EntityNotFoundError: If entity doesn't exist
    """
    if hard_delete:
        # Permanently delete
        try:
            delete_item(entity_id, partition_key=user_id)
        except CosmosResourceNotFoundError:
            raise EntityNotFoundError(f"Entity '{entity_id}' not found")
    else:
        # Soft delete
        entity_doc = get_entity(user_id, entity_id)
        entity_doc["isDeleted"] = True
        entity_doc["deletedAt"] = datetime.utcnow().isoformat() + "Z"
        upsert_item(entity_doc)


def list_entities(
    user_id: str,
    entity_type: str,
    filters: dict[str, Any] | None = None,
    sort_by: str | None = None,
    sort_descending: bool = False,
    limit: int = 50,
    include_deleted: bool = False,
) -> list[dict]:
    """
    List entities of a specific type with optional filtering and sorting.

    Args:
        user_id: User ID (partition key)
        entity_type: Type of entities to list
        filters: Optional filters on data fields (e.g., {"status": "todo"})
        sort_by: Optional field name to sort by (must be in data object)
        sort_descending: Sort in descending order (default: ascending)
        limit: Maximum number of results (default: 50)
        include_deleted: Include soft-deleted entities (default: False)

    Returns:
        List of entity documents

    Example:
        >>> list_entities(
        ...     "user123",
        ...     "task",
        ...     filters={"status": "in-progress"},
        ...     sort_by="dueDate",
        ...     limit=20
        ... )
    """
    # Build query
    query_parts = [
        "SELECT * FROM c WHERE c.userId = @userId",
        "AND c.docType = 'entity'",
        "AND c.entityType = @entityType",
    ]

    parameters = [
        {"name": "@userId", "value": user_id},
        {"name": "@entityType", "value": entity_type},
    ]

    # Filter deleted items unless explicitly included
    if not include_deleted:
        query_parts.append("AND (NOT IS_DEFINED(c.isDeleted) OR c.isDeleted = false)")

    # Add data field filters
    if filters:
        for i, (field_name, field_value) in enumerate(filters.items()):
            param_name = f"@filter{i}"
            query_parts.append(f"AND c.data.{field_name} = {param_name}")
            parameters.append({"name": param_name, "value": field_value})

    # Add sorting
    if sort_by:
        order = "DESC" if sort_descending else "ASC"
        query_parts.append(f"ORDER BY c.data.{sort_by} {order}")

    query = " ".join(query_parts)

    # Execute query with partition key for efficiency
    results = query_items(
        query=query,
        parameters=parameters,
        partition_key=user_id,
        max_item_count=limit,
    )

    return results


def count_entities(user_id: str, entity_type: str, include_deleted: bool = False) -> int:
    """
    Count entities of a specific type.

    Args:
        user_id: User ID
        entity_type: Type of entities to count
        include_deleted: Include soft-deleted entities (default: False)

    Returns:
        Number of entities
    """
    query_parts = [
        "SELECT VALUE COUNT(1) FROM c",
        "WHERE c.userId = @userId",
        "AND c.docType = 'entity'",
        "AND c.entityType = @entityType",
    ]

    parameters = [
        {"name": "@userId", "value": user_id},
        {"name": "@entityType", "value": entity_type},
    ]

    if not include_deleted:
        query_parts.append("AND (NOT IS_DEFINED(c.isDeleted) OR c.isDeleted = false)")

    query = " ".join(query_parts)

    results = query_items(query=query, parameters=parameters, partition_key=user_id)

    return results[0] if results else 0


def get_entities_by_ids(user_id: str, entity_ids: list[str]) -> list[dict]:
    """
    Get multiple entities by their IDs.

    Args:
        user_id: User ID (partition key)
        entity_ids: List of entity IDs

    Returns:
        List of entity documents (excludes not found items)
    """
    if not entity_ids:
        return []

    # Build IN clause
    id_params = [f"@id{i}" for i in range(len(entity_ids))]
    id_clause = ", ".join(id_params)

    query = f"""
        SELECT * FROM c
        WHERE c.userId = @userId
        AND c.docType = 'entity'
        AND c.id IN ({id_clause})
        AND (NOT IS_DEFINED(c.isDeleted) OR c.isDeleted = false)
    """

    parameters = [{"name": "@userId", "value": user_id}]
    parameters.extend([{"name": f"@id{i}", "value": entity_id} for i, entity_id in enumerate(entity_ids)])

    results = query_items(query=query, parameters=parameters, partition_key=user_id)

    return results
