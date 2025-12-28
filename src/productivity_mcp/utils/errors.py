"""
Custom exception classes for the productivity MCP server.
"""


class ProductivityError(Exception):
    """Base exception for all productivity system errors."""

    pass


class CosmosDBError(ProductivityError):
    """Error occurred during Cosmos DB operations."""

    pass


class SchemaError(ProductivityError):
    """Error related to schema definition or validation."""

    pass


class SchemaNotFoundError(SchemaError):
    """Requested schema does not exist."""

    pass


class SchemaValidationError(SchemaError):
    """Schema definition is invalid."""

    pass


class EntityError(ProductivityError):
    """Error related to entity operations."""

    pass


class EntityNotFoundError(EntityError):
    """Requested entity does not exist."""

    pass


class EntityValidationError(EntityError):
    """Entity data does not conform to schema."""

    pass


class EntityTypeNotFoundError(EntityError):
    """Entity type does not exist in user's schema."""

    pass


class AuthenticationError(ProductivityError):
    """Authentication or authorization failed."""

    pass


class ConfigurationError(ProductivityError):
    """Invalid configuration detected."""

    pass
