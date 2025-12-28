"""
Pydantic models for schema definitions.
These models define the structure of user-defined entity type schemas.
"""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


# Supported field types
FieldType = Literal["string", "number", "boolean", "enum", "datetime", "array", "object"]


class FieldDefinition(BaseModel):
    """
    Definition of a single field in an entity schema.

    Examples:
        String field: FieldDefinition(type="string", required=True)
        Enum field: FieldDefinition(type="enum", enum_values=["todo", "done"], default="todo")
        Number field: FieldDefinition(type="number", default=0)
    """

    type: FieldType
    required: bool = False
    default: Any | None = None
    enum_values: list[str] | None = Field(default=None, description="Allowed values for enum type")

    # Phase 2: Support for nested structures
    # array_item_type: FieldType | None = None
    # object_schema: dict[str, "FieldDefinition"] | None = None

    def model_post_init(self, __context: Any) -> None:
        """Validate field definition constraints."""
        # Enum must have enum_values
        if self.type == "enum" and not self.enum_values:
            raise ValueError("Enum fields must specify enum_values")

        # Non-enum shouldn't have enum_values
        if self.type != "enum" and self.enum_values:
            raise ValueError(f"{self.type} fields cannot have enum_values")


class DisplayConfig(BaseModel):
    """
    Optional UI display configuration for an entity type.

    This guides how the UI should render this entity type (Phase 2).
    """

    icon: str | None = None
    color: str | None = None
    default_view: Literal["list", "grid", "kanban", "calendar"] | None = None
    sort_by: str | None = None
    group_by: str | None = None


class EntityTypeSchema(BaseModel):
    """
    Schema definition for a single entity type (e.g., "task", "goal", "habit").

    This defines what fields an entity of this type can have.
    """

    version: int = Field(default=1, description="Schema version for migrations")
    schema: dict[str, FieldDefinition] = Field(description="Field definitions")
    display_config: DisplayConfig | None = Field(default=None, description="UI display hints")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_required_fields(self) -> list[str]:
        """Get list of required field names."""
        return [name for name, field_def in self.schema.items() if field_def.required]

    def get_field_names(self) -> list[str]:
        """Get list of all field names."""
        return list(self.schema.keys())


class UserSchemaDocument(BaseModel):
    """
    Complete schema document for a user.

    This document lives in Cosmos DB and contains all entity type definitions
    for a single user.

    Cosmos document structure:
        {
            "id": "schema:user123",
            "docType": "schema",
            "userId": "user123",
            "version": 1,
            "entityTypes": {
                "task": {...},
                "goal": {...}
            }
        }
    """

    id: str = Field(description="Document ID (format: 'schema:{userId}')")
    doc_type: str = Field(default="schema", alias="docType")
    user_id: str = Field(alias="userId", description="User ID (partition key)")
    version: int = Field(default=1, description="Schema document version")
    entity_types: dict[str, EntityTypeSchema] = Field(default_factory=dict, alias="entityTypes")

    class Config:
        populate_by_name = True  # Allow both field name and alias

    @classmethod
    def create_for_user(cls, user_id: str) -> "UserSchemaDocument":
        """Create a new empty schema document for a user."""
        return cls(
            id=f"schema:{user_id}",
            docType="schema",
            userId=user_id,
            version=1,
            entityTypes={},
        )

    def add_entity_type(
        self,
        entity_type_name: str,
        schema: dict[str, FieldDefinition],
        display_config: DisplayConfig | None = None,
    ) -> None:
        """
        Add a new entity type to the schema.

        Args:
            entity_type_name: Name of the entity type (e.g., "task")
            schema: Field definitions
            display_config: Optional UI configuration

        Raises:
            ValueError: If entity type already exists
        """
        if entity_type_name in self.entity_types:
            raise ValueError(f"Entity type '{entity_type_name}' already exists")

        self.entity_types[entity_type_name] = EntityTypeSchema(
            version=1,
            schema=schema,
            display_config=display_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.version += 1

    def update_entity_type(
        self,
        entity_type_name: str,
        schema_updates: dict[str, FieldDefinition] | None = None,
        display_config: DisplayConfig | None = None,
    ) -> None:
        """
        Update an existing entity type schema.

        Args:
            entity_type_name: Name of the entity type
            schema_updates: Updated field definitions (merged with existing)
            display_config: Updated display config

        Raises:
            ValueError: If entity type doesn't exist
        """
        if entity_type_name not in self.entity_types:
            raise ValueError(f"Entity type '{entity_type_name}' not found")

        entity_schema = self.entity_types[entity_type_name]

        # Merge schema updates
        if schema_updates:
            entity_schema.schema.update(schema_updates)

        # Update display config
        if display_config is not None:
            entity_schema.display_config = display_config

        # Increment versions
        entity_schema.version += 1
        entity_schema.updated_at = datetime.utcnow()
        self.version += 1

    def remove_entity_type(self, entity_type_name: str) -> None:
        """
        Remove an entity type from the schema.

        Args:
            entity_type_name: Name of the entity type

        Raises:
            ValueError: If entity type doesn't exist
        """
        if entity_type_name not in self.entity_types:
            raise ValueError(f"Entity type '{entity_type_name}' not found")

        del self.entity_types[entity_type_name]
        self.version += 1

    def has_entity_type(self, entity_type_name: str) -> bool:
        """Check if entity type exists in schema."""
        return entity_type_name in self.entity_types

    def get_entity_type(self, entity_type_name: str) -> EntityTypeSchema:
        """
        Get entity type schema.

        Args:
            entity_type_name: Name of the entity type

        Returns:
            EntityTypeSchema for the entity type

        Raises:
            ValueError: If entity type doesn't exist
        """
        if entity_type_name not in self.entity_types:
            raise ValueError(f"Entity type '{entity_type_name}' not found")

        return self.entity_types[entity_type_name]
