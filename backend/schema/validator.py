"""
Schema validation logic.
Validates entity data against schema definitions.
"""

from datetime import datetime
from typing import Any

from backend.schema.models import FieldDefinition, EntityTypeSchema
from backend.utils.errors import SchemaValidationError, EntityValidationError


def validate_schema_definition(schema: dict[str, dict]) -> dict[str, FieldDefinition]:
    """
    Validate and parse a schema definition.

    Args:
        schema: Raw schema definition dict

    Returns:
        Parsed FieldDefinition objects

    Raises:
        SchemaValidationError: If schema is invalid

    Example:
        >>> schema = {
        ...     "title": {"type": "string", "required": True},
        ...     "status": {"type": "enum", "enum_values": ["todo", "done"]}
        ... }
        >>> validated = validate_schema_definition(schema)
    """
    if not schema:
        raise SchemaValidationError("Schema cannot be empty")

    if not isinstance(schema, dict):
        raise SchemaValidationError("Schema must be a dictionary")

    try:
        parsed_schema: dict[str, FieldDefinition] = {}

        for field_name, field_spec in schema.items():
            if not isinstance(field_name, str):
                raise SchemaValidationError(f"Field name must be string, got {type(field_name)}")

            if not isinstance(field_spec, dict):
                raise SchemaValidationError(f"Field '{field_name}' specification must be a dictionary")

            # Parse field definition using Pydantic
            try:
                field_def = FieldDefinition(**field_spec)
                parsed_schema[field_name] = field_def
            except Exception as e:
                raise SchemaValidationError(f"Invalid field definition for '{field_name}': {str(e)}")

        return parsed_schema

    except SchemaValidationError:
        raise
    except Exception as e:
        raise SchemaValidationError(f"Schema validation failed: {str(e)}")


def validate_entity_data(data: dict[str, Any], entity_schema: EntityTypeSchema) -> None:
    """
    Validate entity data against its schema.

    Args:
        data: Entity data to validate
        entity_schema: Schema definition for this entity type

    Raises:
        EntityValidationError: If data doesn't conform to schema

    Example:
        >>> schema = EntityTypeSchema(schema={
        ...     "title": FieldDefinition(type="string", required=True),
        ...     "count": FieldDefinition(type="number", default=0)
        ... })
        >>> validate_entity_data({"title": "Test"}, schema)  # OK
        >>> validate_entity_data({}, schema)  # Raises EntityValidationError (missing required 'title')
    """
    # Check required fields
    required_fields = entity_schema.get_required_fields()
    for field_name in required_fields:
        if field_name not in data or data[field_name] is None:
            raise EntityValidationError(f"Required field '{field_name}' is missing or null")

    # Validate each field in data
    for field_name, value in data.items():
        if field_name not in entity_schema.schema:
            raise EntityValidationError(f"Unknown field '{field_name}' not in schema")

        field_def = entity_schema.schema[field_name]

        # Skip validation if value is None and field is not required
        if value is None:
            if field_def.required:
                raise EntityValidationError(f"Required field '{field_name}' cannot be null")
            continue

        # Validate field value type
        _validate_field_value(field_name, value, field_def)


def _validate_field_value(field_name: str, value: Any, field_def: FieldDefinition) -> None:
    """
    Validate a single field value against its definition.

    Args:
        field_name: Name of the field (for error messages)
        value: Field value
        field_def: Field definition

    Raises:
        EntityValidationError: If value doesn't match field type
    """
    field_type = field_def.type

    if field_type == "string":
        if not isinstance(value, str):
            raise EntityValidationError(f"Field '{field_name}' must be a string, got {type(value).__name__}")

    elif field_type == "number":
        if not isinstance(value, (int, float)):
            raise EntityValidationError(f"Field '{field_name}' must be a number, got {type(value).__name__}")

    elif field_type == "boolean":
        if not isinstance(value, bool):
            raise EntityValidationError(f"Field '{field_name}' must be a boolean, got {type(value).__name__}")

    elif field_type == "enum":
        if not isinstance(value, str):
            raise EntityValidationError(f"Enum field '{field_name}' must be a string, got {type(value).__name__}")

        if field_def.enum_values and value not in field_def.enum_values:
            allowed = ", ".join(field_def.enum_values)
            raise EntityValidationError(
                f"Field '{field_name}' must be one of [{allowed}], got '{value}'"
            )

    elif field_type == "datetime":
        # Accept datetime objects or ISO 8601 strings
        if isinstance(value, datetime):
            return  # Valid datetime object

        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise EntityValidationError(
                    f"Field '{field_name}' must be a valid ISO 8601 datetime string, got '{value}'"
                )
        else:
            raise EntityValidationError(
                f"Field '{field_name}' must be a datetime or ISO string, got {type(value).__name__}"
            )

    elif field_type == "array":
        if not isinstance(value, list):
            raise EntityValidationError(f"Field '{field_name}' must be an array, got {type(value).__name__}")
        # Phase 2: Validate array item types

    elif field_type == "object":
        if not isinstance(value, dict):
            raise EntityValidationError(f"Field '{field_name}' must be an object, got {type(value).__name__}")
        # Phase 2: Validate nested object schema

    else:
        raise EntityValidationError(f"Unknown field type '{field_type}' for field '{field_name}'")


def apply_defaults(data: dict[str, Any], entity_schema: EntityTypeSchema) -> dict[str, Any]:
    """
    Apply default values for fields not provided in data.

    Args:
        data: Entity data (will not be modified)
        entity_schema: Schema definition

    Returns:
        New dict with defaults applied

    Example:
        >>> schema = EntityTypeSchema(schema={
        ...     "title": FieldDefinition(type="string", required=True),
        ...     "count": FieldDefinition(type="number", default=0)
        ... })
        >>> apply_defaults({"title": "Test"}, schema)
        {'title': 'Test', 'count': 0}
    """
    result = data.copy()

    for field_name, field_def in entity_schema.schema.items():
        # Apply default if field not in data and default is defined
        if field_name not in result and field_def.default is not None:
            result[field_name] = field_def.default

    return result


def validate_and_apply_defaults(data: dict[str, Any], entity_schema: EntityTypeSchema) -> dict[str, Any]:
    """
    Validate entity data and apply default values.

    This is the main entry point for entity validation.

    Args:
        data: Entity data to validate
        entity_schema: Schema definition

    Returns:
        Validated data with defaults applied

    Raises:
        EntityValidationError: If validation fails
    """
    # Apply defaults first
    data_with_defaults = apply_defaults(data, entity_schema)

    # Then validate
    validate_entity_data(data_with_defaults, entity_schema)

    return data_with_defaults
