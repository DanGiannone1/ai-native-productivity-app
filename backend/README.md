# Productivity MCP Server - Code Architecture

**Source of truth for code structure, modules, and design patterns.**

> **Note:** This directory will be migrated to `src/productivity_mcp/` in Phase 2 of the enterprise alignment. For now, documentation reflects the current `backend/` structure.

---

## Overview

The Productivity MCP Server is a FastMCP-based service that provides AI-driven, schema-flexible productivity data management. It allows Claude to dynamically create and manage custom entity types based on user mental models.

**Key Capabilities:**
- Dynamic schema creation (tasks, goals, habits, custom types)
- Multi-document Cosmos DB architecture (scales indefinitely)
- MCP protocol for Claude Desktop integration
- Schema validation and versioning
- Development mode with auth bypass

---

## Architecture Principles

### 1. Schema Flexibility
- Users define their own entity types (no rigid schemas)
- AI interprets user intent and creates appropriate schemas
- Each user has isolated data (partitioned by `userId`)

### 2. Multi-Document Design
- **Schema documents**: Store entity type definitions
- **Entity documents**: Store individual instances
- Efficient queries (no 2MB document limit)
- Lower RU costs (update one entity, not entire user state)

### 3. Separation of Concerns
- **Tools**: MCP tool definitions and decorators
- **Services**: Business logic for schema and entity operations
- **Schema**: Validation and models
- **Auth**: Authentication (dev mode + future Scalekit OAuth)
- **Utils**: Cross-cutting concerns (telemetry, errors)

---

## Module Structure

```
backend/
├── __init__.py
├── __main__.py              # Module entry point
├── mcp_server.py            # FastMCP server & tool registration
├── config.py                # Environment configuration
├── cosmos_client.py         # Cosmos DB singleton client
│
├── auth/
│   ├── __init__.py
│   └── dev_auth.py          # Dev-mode auth bypass
│
├── schema/
│   ├── __init__.py
│   ├── models.py            # Pydantic schema models
│   └── validator.py         # Schema validation logic
│
├── services/
│   ├── __init__.py
│   ├── schema_service.py    # Schema CRUD operations
│   └── entity_service.py    # Entity CRUD operations
│
├── tools/
│   ├── __init__.py
│   ├── schema_tools.py      # MCP schema management tools
│   └── entity_tools.py      # MCP entity CRUD tools
│
└── utils/
    ├── __init__.py
    ├── errors.py            # Custom exceptions
    └── telemetry.py         # Logging decorators
```

---

## Key Modules

### `mcp_server.py` - FastMCP Server Entry Point

**Purpose:** Initialize FastMCP server and register MCP tools

**Key Components:**
- FastMCP server initialization
- Tool registration (10 core tools)
- Logging configuration
- ASGI app export for uvicorn

**Tools Registered:**
- **Schema Management:** `create_entity_type`, `get_user_schema`, `update_entity_type`, `delete_entity_type`
- **Entity CRUD:** `create_entity`, `get_entity`, `update_entity`, `list_entities`, `delete_entity`, `count_entities`

**Run:** `python -m backend.mcp_server` or `.\run_local.ps1 mcp`

---

### `config.py` - Configuration Management

**Purpose:** Load and validate environment variables

**Key Settings:**
- `COSMOS_HOST`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER`
- `DISABLE_AUTH`, `DEFAULT_USER_ID` (dev mode)
- `SCALEKIT_*` (future OAuth integration)
- `LOG_LEVEL`

**Validation:** Runs on module import, fails fast if required vars missing

---

### `cosmos_client.py` - Cosmos DB Client Singleton

**Purpose:** Provide singleton access to Cosmos DB resources

**Pattern:** Lazy initialization with global caching

**Functions:**
- `get_cosmos_client()` → CosmosClient
- `get_database()` → DatabaseProxy
- `get_container()` → ContainerProxy
- `create_database_if_not_exists()`
- `create_container_if_not_exists()`
- `query_items()`, `create_item()`, `read_item()`, `upsert_item()`, `delete_item()`

**Partition Strategy:** All documents partitioned by `/userId` for efficient single-partition queries

---

### `schema/` - Schema Management

#### `models.py` - Pydantic Data Models

**Core Models:**
- `FieldDefinition`: Defines a single field in an entity type schema
- `EntityTypeSchema`: Complete entity type definition with versioning
- `UserSchemaDocument`: Cosmos DB schema document (docType: "schema")
- `EntityDocument`: Cosmos DB entity document (docType: "entity")

**Design:** Uses Pydantic for validation and serialization

#### `validator.py` - Schema Validation

**Purpose:** Validate entity data against schema definitions

**Key Function:**
- `validate_entity_data(data: dict, schema: dict) → tuple[bool, list[str]]`
- Checks required fields, type consistency, enum values
- Returns validation status and error messages

---

### `services/` - Business Logic

#### `schema_service.py` - Schema CRUD

**Functions:**
- `create_entity_type()`: Define new entity type
- `get_user_schema()`: Retrieve all entity type definitions
- `update_entity_type()`: Modify existing schema
- `delete_entity_type()`: Remove entity type

**Cosmos Operations:**
- Upserts schema document (`id: "schema:{userId}"`)
- Increments version on updates
- Validates schema structure

#### `entity_service.py` - Entity CRUD

**Functions:**
- `create_entity()`: Create new entity instance
- `get_entity()`: Retrieve by ID
- `update_entity()`: Partial update
- `list_entities()`: Query with filtering/sorting
- `delete_entity()`: Soft or hard delete
- `count_entities()`: Count entities of type

**Cosmos Operations:**
- Creates entity documents (`id: "{entityType}:{uuid}"`)
- Validates against schema before create/update
- Supports filters, sorting, pagination

---

### `tools/` - MCP Tool Definitions

#### `schema_tools.py` - Schema Management Tools

**Exports:**
- `create_entity_type_tool()`
- `get_user_schema_tool()`
- `update_entity_type_tool()`
- `delete_entity_type_tool()`

**Pattern:** Tools call service functions, return structured responses

#### `entity_tools.py` - Entity CRUD Tools

**Exports:**
- `create_entity_tool()`
- `get_entity_tool()`
- `update_entity_tool()`
- `list_entities_tool()`
- `delete_entity_tool()`
- `count_entities_tool()`

**Pattern:** Tools validate inputs, call services, handle errors gracefully

---

### `auth/` - Authentication

#### `dev_auth.py` - Development Authentication

**Purpose:** Auth bypass for MVP (no OAuth required)

**Current State:**
- Returns `DEFAULT_USER_ID` for all requests
- Future: Scalekit OAuth integration (Phase 2)

**Config:**
- `DISABLE_AUTH=true` enables dev mode
- `DEFAULT_USER_ID=dev-user` sets default user

---

### `utils/` - Cross-Cutting Utilities

#### `errors.py` - Custom Exceptions

**Exceptions:**
- `CosmosDBError`: Cosmos DB operation failures
- `SchemaValidationError`: Schema validation failures
- `EntityNotFoundError`: Entity lookup failures

**Pattern:** Domain-specific exceptions for clear error handling

#### `telemetry.py` - Logging Decorators

**Decorator:**
- `@with_telemetry(operation_name)`: Logs duration, success/failure
- Structured logging with operation IDs
- Error context preservation

**Usage:**
```python
@with_telemetry("create_task")
def create_task(...):
    ...
```

---

## Design Patterns

### 1. Singleton Pattern
- **Cosmos DB Client**: Global singleton with lazy initialization
- **Rationale**: Expensive to create, shared across all operations

### 2. Service Layer Pattern
- **Services**: Encapsulate business logic
- **Tools**: Thin wrappers that call services
- **Rationale**: Separation of MCP protocol from business logic

### 3. Schema Validation Pattern
- **Validate before write**: All entity operations validate against schema
- **Fail fast**: Return errors immediately, don't persist invalid data
- **Rationale**: Data integrity, clear error messages

### 4. Multi-Document Pattern
- **Schema doc**: `id: "schema:{userId}", docType: "schema"`
- **Entity docs**: `id: "{entityType}:{uuid}", docType: "entity"`
- **Rationale**: Scales indefinitely, efficient queries, lower costs

### 5. Telemetry Decorator Pattern
- **Aspect-oriented**: Cross-cutting logging concern
- **Consistent**: All service functions instrumented
- **Rationale**: Observability without cluttering business logic

---

## Data Model

### Schema Document
```json
{
  "id": "schema:dev-user",
  "docType": "schema",
  "userId": "dev-user",
  "version": 1,
  "entityTypes": {
    "task": {
      "version": 1,
      "schema": {
        "title": {"type": "string", "required": true},
        "status": {"type": "enum", "enum_values": ["todo", "done"]},
        "dueDate": {"type": "datetime"}
      }
    }
  }
}
```

### Entity Document
```json
{
  "id": "task:abc-123",
  "docType": "entity",
  "userId": "dev-user",
  "entityType": "task",
  "version": 1,
  "data": {
    "title": "Review metrics",
    "status": "todo",
    "dueDate": "2025-12-30T17:00:00Z"
  },
  "createdAt": "2025-12-27T10:00:00Z",
  "updatedAt": "2025-12-27T10:00:00Z"
}
```

---

## Common Operations

### Adding a New MCP Tool

1. **Define tool function** in `tools/` directory
2. **Implement service logic** in `services/`
3. **Register tool** in `mcp_server.py` with `@mcp.tool()`
4. **Add telemetry** with `@with_telemetry()`
5. **Test** with `.\run_local.ps1 test`

### Adding a New Entity Type (via MCP)

1. **Claude calls** `create_entity_type()`
2. **Schema service** validates and stores schema
3. **Entities created** with `create_entity()` validated against schema

### Querying Entities

- **Single-partition query** (efficient): Provide `userId` as partition key
- **Cross-partition query** (expensive): Omit partition key, higher RU cost

---

## Testing Strategy

See `tests/README.md` for comprehensive testing documentation.

**Quick Test:**
```powershell
.\run_local.ps1 test
```

**Local MCP Test:**
```powershell
.\run_local.ps1 mcp
# In another terminal:
.\run_local.ps1 test-mcp
```

---

## Future Architecture

### Phase 2: Scalekit OAuth Integration
- Replace `dev_auth.py` with Scalekit OAuth provider
- Add scope validation (Read, Write)
- M2M client whitelist for testing

### Phase 2: Relationships Between Entities
- Foreign key pattern for entity references
- Link entity types (e.g., task → goal)

### Phase 3: Event Sourcing
- Entity history tracking
- Audit log of all changes

---

## Related Documentation

- **Root README**: [../README.md](../README.md) - Project overview and quick start
- **Deployment**: [../deployment/README.md](../deployment/README.md) - Infrastructure and deployment
- **Security**: [../security/README.md](../security/README.md) - Authentication and authorization
- **Monitoring**: [../monitoring/README.md](../monitoring/README.md) - Observability and logging
- **Tests**: [../tests/README.md](../tests/README.md) - Testing strategy

**Agent Instructions**: [../CLAUDE.md](../CLAUDE.md)

---

**Last Updated:** 2025-12-27 (Phase 1: Enterprise Alignment)
