# Source Code - Productivity MCP Server

> **Note**: This README documents the architecture currently implemented in `backend/`. In Phase 2, the codebase will be migrated to `src/productivity_mcp/` following enterprise standards.

## Overview

This directory contains the **Productivity MCP Server** - an AI-driven, schema-flexible productivity system built with FastMCP and Azure Cosmos DB.

**Key Characteristics:**
- **Schema-Flexible**: No rigid schemas. AI interprets user intent and creates entity types dynamically.
- **MCP Protocol**: Exposes productivity tools via Model Context Protocol for AI agents.
- **Cosmos DB Backend**: Multi-document NoSQL design partitioned by user ID.
- **Python Stack**: FastMCP 2.2.0, Azure Cosmos SDK 4.7.0, Pydantic 2.10.4, Uvicorn.

**Current Location**: `backend/` (will migrate to `src/productivity_mcp/` in Phase 2)

---

## Architecture

The system follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│   MCP Server Layer (FastMCP + Uvicorn)      │  ← SSE transport, 10 tools
├─────────────────────────────────────────────┤
│   Tools Layer (schema_tools, entity_tools)  │  ← Thin MCP wrappers
├─────────────────────────────────────────────┤
│   Service Layer (schema_service, entity_   │  ← Business logic
│                  service)                    │
├─────────────────────────────────────────────┤
│   Repository Layer (cosmos_client)          │  ← DB abstraction
├─────────────────────────────────────────────┤
│   Schema Layer (models, validator)          │  ← Type definitions, validation
├─────────────────────────────────────────────┤
│   Infrastructure (config, auth, utils)      │  ← Cross-cutting concerns
└─────────────────────────────────────────────┘
           ↓
    Azure Cosmos DB
```

**Design Philosophy:**
- **Separation of Concerns**: Tools → Services → Repository → Database
- **Pydantic-First**: Strong typing with models for schemas and entities
- **AI-Friendly**: Tools designed for LLM consumption (clear params, helpful errors)
- **Single-Partition Queries**: `/userId` partitioning for query efficiency

---

## Module Organization

Current structure (in `backend/`):

```
backend/                     (Future: src/productivity_mcp/)
│
├── mcp_server.py           # Main FastMCP server entry point
│                           # - Exports 10 MCP tools (4 schema + 6 entity)
│                           # - Logging configuration
│                           # - ASGI app for Uvicorn
│
├── cosmos_client.py        # Singleton Cosmos DB client
│                           # - get_cosmos_client(), get_database(), get_container()
│                           # - CRUD: create_item, read_item, upsert_item, delete_item
│                           # - query_items with partition key support
│
├── config.py               # Environment-based configuration
│                           # - Loads .env file
│                           # - Validates required settings on import
│                           # - Config.is_dev_mode() for auth bypass
│
├── services/
│   ├── __init__.py
│   ├── schema_service.py   # Schema document management
│   │                       # - get_user_schema, create_entity_type
│   │                       # - update_entity_type, delete_entity_type
│   │                       # - Returns UserSchemaDocument Pydantic models
│   │
│   └── entity_service.py   # Entity CRUD operations
│                           # - create_entity, get_entity, update_entity
│                           # - list_entities (with filters, sorting, limits)
│                           # - delete_entity (soft or hard delete)
│                           # - Validates against schema before save
│
├── schema/
│   ├── __init__.py
│   ├── models.py           # Pydantic models for schema definitions
│   │                       # - FieldDefinition (type, required, default, enum_values)
│   │                       # - EntityTypeSchema (version, schema, display_config)
│   │                       # - UserSchemaDocument (complete user schema doc)
│   │
│   └── validator.py        # Schema and entity validation logic
│                           # - validate_schema_definition (checks field types)
│                           # - validate_entity_data (enforces schema)
│                           # - apply_defaults, validate_and_apply_defaults
│
├── tools/
│   ├── __init__.py
│   ├── schema_tools.py     # MCP tools for schema management
│   │                       # - create_entity_type_tool, get_user_schema_tool
│   │                       # - update_entity_type_tool, delete_entity_type_tool
│   │                       # - Thin wrappers around schema_service
│   │
│   └── entity_tools.py     # MCP tools for entity CRUD
│                           # - create_entity_tool, get_entity_tool, update_entity_tool
│                           # - list_entities_tool, delete_entity_tool, count_entities_tool
│                           # - Thin wrappers around entity_service
│
├── auth/
│   ├── __init__.py
│   └── dev_auth.py         # Development authentication bypass
│                           # - get_current_user() returns DEFAULT_USER_ID
│                           # - Phase 2: Replace with Scalekit OAuth
│
└── utils/
    ├── __init__.py
    ├── errors.py           # Custom exception classes
    │                       # - CosmosDBError, SchemaValidationError
    │                       # - EntityNotFoundError, EntityTypeNotFoundError
    │
    └── telemetry.py        # Logging and monitoring utilities
                            # - Phase 2: Azure Monitor integration
```

---

## Key Design Patterns

### 1. Singleton Cosmos Client
**File**: `cosmos_client.py`

Module-level singletons for connection reuse:
```python
_cosmos_client: CosmosClient | None = None
_database: DatabaseProxy | None = None
_container: ContainerProxy | None = None
```

**Why**: Avoid recreating Cosmos connections on every request. Single client instance per server lifetime.

### 2. Repository Pattern
**File**: `cosmos_client.py`

Abstracts Cosmos DB operations with clean interface:
- `create_item(item)`, `read_item(id, partition_key)`
- `upsert_item(item)`, `delete_item(id, partition_key)`
- `query_items(query, parameters, partition_key)`

**Why**: Services don't know about Cosmos SDK details. Easy to mock for testing.

### 3. Service Layer Pattern
**Files**: `services/schema_service.py`, `services/entity_service.py`

Business logic separate from MCP tools:
- Tools validate input, call service methods, format responses
- Services orchestrate operations (validation → DB → response)
- Services return Pydantic models or raise domain exceptions

**Why**: Tools are thin protocol adapters. Core logic is reusable beyond MCP.

### 4. Tool Decorator Pattern
**File**: `mcp_server.py`

FastMCP decorators expose Python functions as MCP tools:
```python
@mcp.tool()
def create_entity_type(entity_type_name: str, schema_definition: dict, ...) -> dict:
    # Docstring becomes tool description for AI
    # Type hints guide parameter validation
    return create_entity_type_tool(...)
```

**Why**: Clean separation between MCP protocol and business logic.

### 5. Pydantic Models
**File**: `schema/models.py`

Strong typing with validation:
- `FieldDefinition`: Validates field types, enum constraints
- `EntityTypeSchema`: Manages schema versions
- `UserSchemaDocument`: Complete schema with CRUD methods

**Why**: Catch errors early. Self-documenting schemas. Easy serialization to/from Cosmos.

### 6. Partition Key Design
**All DB Operations**

Partition key: `/userId`

All queries use `partition_key=user_id` for single-partition efficiency.

**Why**: User data stays in one partition → no cross-partition queries → lower RU costs.

### 7. Multi-Document Model
**Cosmos DB Design**

Two document types in same container:
- **Schema**: `{id: "schema:{userId}", docType: "schema", entityTypes: {...}}`
- **Entity**: `{id: "{entityType}:{uuid}", docType: "entity", data: {...}}`

Use `docType` field for discriminated queries.

**Why**: Schema-flexible. No rigid table structure. AI can create new entity types dynamically.

### 8. Soft Delete Pattern
**File**: `services/entity_service.py`

Entities have `isDeleted` flag:
- Soft delete: Set `isDeleted=True`, add `deletedAt` timestamp
- Hard delete: Actually remove from Cosmos
- Default queries filter `WHERE isDeleted = false`

**Why**: Recovery from accidental deletes. Audit trail.

---

## Data Model

### Cosmos DB Structure

**Container**: `productivity-data` (or `Config.COSMOS_CONTAINER`)
**Partition Key**: `/userId`
**Documents**: Schema and Entity documents in same container

### Schema Document

Stores all entity type definitions for a user:

```json
{
  "id": "schema:user123",
  "docType": "schema",
  "userId": "user123",
  "version": 3,
  "entityTypes": {
    "task": {
      "version": 1,
      "schema": {
        "title": {"type": "string", "required": true},
        "status": {
          "type": "enum",
          "enum_values": ["todo", "in-progress", "done"],
          "default": "todo"
        },
        "priority": {
          "type": "enum",
          "enum_values": ["low", "medium", "high"]
        },
        "dueDate": {"type": "datetime"}
      },
      "display_config": {
        "icon": "task-icon",
        "color": "#4A90E2",
        "default_view": "list",
        "sort_by": "dueDate"
      },
      "created_at": "2025-12-27T10:00:00Z",
      "updated_at": "2025-12-27T10:00:00Z"
    },
    "goal": { ... }
  }
}
```

**Key Points**:
- One schema doc per user (id: `schema:{userId}`)
- `entityTypes` is a map of type name → schema definition
- Schema versions tracked (for migrations)
- Display config guides UI rendering (Phase 2)

### Entity Document

Stores individual productivity items:

```json
{
  "id": "task:abc-123-def-456",
  "docType": "entity",
  "userId": "user123",
  "entityType": "task",
  "version": 2,
  "data": {
    "title": "Review Q4 metrics",
    "status": "in-progress",
    "priority": "high",
    "dueDate": "2025-12-30T17:00:00Z"
  },
  "metadata": {
    "createdBy": "ai-assistant",
    "aiContext": "From standup discussion"
  },
  "isDeleted": false,
  "createdAt": "2025-12-27T08:00:00Z",
  "updatedAt": "2025-12-27T14:30:00Z"
}
```

**Key Points**:
- ID format: `{entityType}:{uuid}` (enables type-scoped IDs)
- `data` field contains schema-validated entity data
- `metadata` for AI context, provenance tracking
- `isDeleted` for soft deletes
- Version tracking for optimistic concurrency (future)

### Supported Field Types

From `schema/models.py`:

| Type       | Python Type     | Example Values                          |
|------------|-----------------|-----------------------------------------|
| `string`   | `str`           | `"Task title"`                          |
| `number`   | `int`, `float`  | `42`, `3.14`                            |
| `boolean`  | `bool`          | `true`, `false`                         |
| `enum`     | `str`           | `"todo"` (must be in `enum_values`)     |
| `datetime` | `str`, `datetime` | `"2025-12-27T10:00:00Z"` (ISO 8601)   |
| `array`    | `list`          | `["tag1", "tag2"]` (Phase 2: typed arrays) |
| `object`   | `dict`          | `{"nested": "data"}` (Phase 2: nested schemas) |

---

## Configuration

### Environment Variables

Loaded from `.env` file via `python-dotenv`.

**Required**:
- `COSMOS_HOST` - Cosmos DB endpoint (e.g., `https://myaccount.documents.azure.com:443/`)
- `COSMOS_KEY` - Cosmos DB primary key (secret)
- `COSMOS_DATABASE` - Database name (default: `productivity`)
- `COSMOS_CONTAINER` - Container name (default: `productivity-data`)

**Optional**:
- `ENVIRONMENT` - Environment name (`dev`, `prod`) (default: `dev`)
- `DISABLE_AUTH` - Disable authentication for dev (`true`/`false`) (default: `false`)
- `DEFAULT_USER_ID` - User ID for dev mode (default: `dev-user`)
- `LOG_LEVEL` - Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) (default: `INFO`)

**Phase 2 (OAuth)**:
- `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`
- `SCALEKIT_RESOURCE_ID`, `MCP_URL`, `AUTHORIZED_M2M_CLIENTS`

### Validation

`config.py` validates required config on module import:
```python
Config.validate()  # Raises ValueError if COSMOS_* missing
```

Fail-fast approach prevents runtime errors.

---

## Development Workflow

### Running Locally

**Option 1: PowerShell script** (recommended)
```powershell
.\run_local.ps1 mcp
```

**Option 2: Direct Python**
```bash
python -m backend.mcp_server
# or
uvicorn backend.mcp_server:app --host 0.0.0.0 --port 8000
```

**Server Details**:
- Protocol: MCP over SSE (Server-Sent Events)
- Port: 8000
- Transport: `mcp.sse_app()` from FastMCP
- Logs: Stdout (structured logs via logging module)

### Testing Tools

MCP tools are exposed via the MCP protocol. Test using:

1. **MCP Client**: Connect Claude Desktop or other MCP clients to `http://localhost:8000`
2. **Direct HTTP**: SSE endpoints (see FastMCP docs for raw protocol)
3. **Python REPL**: Import and call tool functions directly

Example Python testing:
```python
from backend.tools.schema_tools import create_entity_type_tool
from backend.auth.dev_auth import get_current_user

result = create_entity_type_tool(
    "task",
    {
        "title": {"type": "string", "required": True},
        "status": {"type": "enum", "enum_values": ["todo", "done"], "default": "todo"}
    }
)
print(result)
```

### Available MCP Tools

**Schema Management** (4 tools):
1. `create_entity_type` - Define new entity types (e.g., task, goal, habit)
2. `get_user_schema` - Retrieve all entity type definitions
3. `update_entity_type` - Modify existing schemas
4. `delete_entity_type` - Remove entity types (with confirmation)

**Entity CRUD** (6 tools):
1. `create_entity` - Create new entities (validated against schema)
2. `get_entity` - Retrieve entity by ID
3. `update_entity` - Update existing entities (partial updates)
4. `list_entities` - List entities with filters, sorting, limits
5. `delete_entity` - Delete entities (soft or hard delete)
6. `count_entities` - Count entities of a specific type

See `mcp_server.py` for detailed tool documentation.

---

## Future Migration (Phase 2)

### Directory Restructure

**Current**: `backend/` (flat structure)
**Phase 2**: `src/productivity_mcp/` (enterprise structure)

```
src/
└── productivity_mcp/
    ├── __init__.py
    ├── server.py           (was: mcp_server.py)
    ├── cosmos_db.py        (was: cosmos_client.py)
    ├── config.py
    ├── services/
    ├── schema/
    ├── tools/
    ├── auth/               (add: OAuth implementation)
    └── utils/
```

### Planned Enhancements

1. **Authentication**: Replace `dev_auth.py` with Scalekit OAuth
2. **Nested Schemas**: Support for `array` item types and `object` nested schemas
3. **Relationships**: Entity references (e.g., task → goal)
4. **Search**: Full-text search via Cosmos DB or Azure AI Search
5. **Telemetry**: Azure Monitor integration for logs, metrics, traces
6. **Container Apps**: Deploy to Azure Container Apps (see `deployment/`)
7. **Security**: Secrets in Azure Key Vault (see `security/`)

### Migration Checklist

- [ ] Move `backend/` → `src/productivity_mcp/`
- [ ] Update import paths in all files
- [ ] Update `pyproject.toml` `packages` config
- [ ] Update `run_local.ps1` and deployment scripts
- [ ] Add OAuth authentication via Scalekit
- [ ] Integrate Azure Monitor telemetry
- [ ] Update CI/CD pipelines

---

## Related Documentation

- **deployment/README.md** - Infrastructure setup (Cosmos DB, Container Apps, 3-RG silo)
- **security/README.md** - OAuth configuration, secrets management, Key Vault (Phase 2)
- **monitoring/README.md** - Azure Monitor, Application Insights, dashboards (Phase 2)
- **CLAUDE.md** - Project rules, multi-agent workflow, coding standards
- **.claude/rules/guidelines.md** - Naming conventions, code structure
- **.claude/rules/best-practices.md** - DRY, KISS, YAGNI, security practices
- **ENTERPRISE_ALIGNMENT_PLAN.md** - Phased migration plan to enterprise structure

---

## Key Dependencies

From `pyproject.toml`:

| Package                | Version | Purpose                              |
|------------------------|---------|--------------------------------------|
| `fastmcp`              | 2.2.0   | MCP protocol server framework        |
| `azure-cosmos`         | 4.7.0   | Azure Cosmos DB SDK                  |
| `uvicorn[standard]`    | 0.32.1  | ASGI server for FastMCP              |
| `pydantic`             | 2.10.4  | Data validation and schema models    |
| `python-dotenv`        | 1.0.1   | Load .env configuration              |
| `ruff` (dev)           | 0.8.4   | Linter and formatter                 |
| `mypy` (dev)           | 1.13.0  | Static type checking                 |
| `pytest` (dev)         | 8.3.4   | Testing framework                    |

**Python Version**: `>=3.11`

---

## Questions?

- **Architecture questions**: See this README or `ENTERPRISE_ALIGNMENT_PLAN.md`
- **Coding standards**: See `CLAUDE.md` and `.claude/rules/`
- **Deployment**: See `deployment/README.md`
- **Multi-agent workflow**: See `.claude/agents/orchestrator.md`

**AI Agents**: This README is designed to be AI-agent-friendly. If implementing changes, **always use the orchestrator agent** per `CLAUDE.md` to ensure thorough planning and validation.

---

*Last Updated: 2025-12-27*
*Phase: 1 (Initial Implementation)*
*Current Location: `backend/` → Phase 2 Migration: `src/productivity_mcp/`*
