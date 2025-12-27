# Productivity MCP Server

**AI-Driven Schema-Flexible Productivity System**

A FastMCP server that allows Claude to dynamically create and manage each user's unique productivity data model. Users describe their mental model in natural language; Claude translates this into appropriate schemas and manages their data via MCP tools.

## 🎯 The Problem This Solves

Every productivity app forces users into a rigid structure (tasks, projects, tags, etc.). But people think differently:
- Some organize by "habits" and "streaks"
- Others think in "goals" and "milestones"
- Some want "learning resources" with "completion percentage"
- Many need custom combinations

**This system lets Claude create the perfect productivity model for each user on-the-fly.**

## 🏗️ Architecture

### Multi-Document Cosmos DB Design
- **Partition Strategy**: `partitionKey = userId`
- **Document Types**:
  - `schema` - User's entity type definitions (task, goal, habit, etc.)
  - `entity` - Individual instances (one doc per task/goal/etc.)

**Why multi-document?**
- ✅ Scales indefinitely (no 2MB document limit)
- ✅ Efficient queries (don't load all data)
- ✅ Lower RU costs (update one task, not entire user state)
- ✅ Supports recurring task history growth

### MCP Server (FastMCP + Azure Cosmos)

**10 Core Tools**:

**Schema Management**:
- `create_entity_type` - Define new entity types
- `get_user_schema` - View all entity type definitions
- `update_entity_type` - Modify existing schemas
- `delete_entity_type` - Remove entity types

**Entity CRUD**:
- `create_entity` - Create new entities
- `get_entity` - Retrieve by ID
- `update_entity` - Modify entities
- `list_entities` - Query with filtering/sorting
- `delete_entity` - Soft or hard delete
- `count_entities` - Count entities of a type

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Azure Cosmos DB account
- [UV package manager](https://docs.astral.sh/uv/)

### Installation

1. **Clone and setup**:
```powershell
cd C:\projects\productivity
uv sync
```

2. **Configure environment**:
```powershell
cp .env.example .env
# Edit .env with your Cosmos DB credentials
```

3. **Initialize database**:
```powershell
.\run_local.ps1 init
```

4. **Start MCP server**:
```powershell
.\run_local.ps1 mcp
```

Server starts on `http://localhost:8000`

### Configuration (`.env`)

```env
# Cosmos DB (Required)
COSMOS_HOST=https://your-cosmos-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key-here
COSMOS_DATABASE=productivity
COSMOS_CONTAINER=productivity-data

# Development Mode (for MVP)
DISABLE_AUTH=true
DEFAULT_USER_ID=dev-user
```

## 💡 Usage Examples

### Example 1: Habit Tracking System

**User**: "Create a system for tracking my daily habits"

**Claude** (via MCP):
```python
# 1. Create schema
create_entity_type(
    "habit",
    {
        "name": {"type": "string", "required": True},
        "frequency": {"type": "enum", "enum_values": ["daily", "weekly", "monthly"]},
        "streak": {"type": "number", "default": 0},
        "lastCompleted": {"type": "datetime"}
    }
)

# 2. Create entities
create_entity("habit", {
    "name": "Morning meditation",
    "frequency": "daily",
    "streak": 7
})

create_entity("habit", {
    "name": "Weekly review",
    "frequency": "weekly",
    "streak": 3
})

# 3. Query habits
list_entities("habit", sort_by="streak", sort_descending=True)
```

### Example 2: Goal & Milestone System

**User**: "I want to track long-term goals with milestones"

**Claude**:
```python
# Define goal schema
create_entity_type(
    "goal",
    {
        "title": {"type": "string", "required": True},
        "targetDate": {"type": "datetime"},
        "status": {
            "type": "enum",
            "enum_values": ["active", "achieved", "abandoned"],
            "default": "active"
        },
        "milestones": {"type": "array"}
    }
)

# Create a goal
create_entity("goal", {
    "title": "Ship MVP by end of Q1",
    "targetDate": "2025-03-31T00:00:00Z",
    "milestones": [
        {"title": "Complete backend", "done": True},
        {"title": "Build UI", "done": False},
        {"title": "Deploy to production", "done": False}
    ]
})
```

### Example 3: Task Management with Priorities

**User**: "I need a task system with priority levels and due dates"

**Claude**:
```python
create_entity_type(
    "task",
    {
        "title": {"type": "string", "required": True},
        "description": {"type": "string"},
        "status": {
            "type": "enum",
            "enum_values": ["todo", "in-progress", "done"],
            "default": "todo"
        },
        "priority": {
            "type": "enum",
            "enum_values": ["low", "medium", "high", "urgent"]
        },
        "dueDate": {"type": "datetime"},
        "tags": {"type": "array"}
    }
)

# Create high-priority task
create_entity("task", {
    "title": "Review Q4 metrics",
    "status": "in-progress",
    "priority": "high",
    "dueDate": "2025-12-30T17:00:00Z",
    "tags": ["work", "quarterly-review"]
})

# Query in-progress tasks
list_entities(
    "task",
    filters={"status": "in-progress"},
    sort_by="dueDate",
    limit=20
)
```

## 🧪 Testing

### Run Tests
```powershell
.\run_local.ps1 test
```

### Seed Sample Data
```powershell
.\run_local.ps1 seed
```

This creates 3 sample entity types (task, goal, habit) with realistic data.

## 📂 Project Structure

```
C:\projects\productivity\
├── backend/                      # Python backend
│   ├── mcp_server.py            # FastMCP entry point
│   ├── config.py                # Configuration
│   ├── cosmos_client.py         # Cosmos DB client
│   │
│   ├── auth/
│   │   └── dev_auth.py         # Dev-mode auth bypass
│   │
│   ├── schema/
│   │   ├── models.py           # Pydantic schema models
│   │   └── validator.py        # Schema validation
│   │
│   ├── services/
│   │   ├── schema_service.py   # Schema CRUD
│   │   └── entity_service.py   # Entity CRUD
│   │
│   ├── tools/
│   │   ├── schema_tools.py     # MCP schema tools
│   │   └── entity_tools.py     # MCP entity tools
│   │
│   └── utils/
│       ├── errors.py           # Custom exceptions
│       └── telemetry.py        # Logging decorator
│
├── scripts/
│   ├── init_cosmos.py          # DB initialization
│   └── seed_data.py            # Sample data
│
├── tests/
│   └── fixtures/
│       └── sample_schemas.json # Sample schemas
│
├── .env.example                 # Environment template
├── pyproject.toml              # UV dependencies
├── run_local.ps1               # Local runner
└── README.md                   # This file
```

## 🔧 Development

### Available Commands

```powershell
.\run_local.ps1 mcp       # Start MCP server
.\run_local.ps1 init      # Initialize Cosmos DB
.\run_local.ps1 seed      # Seed sample data
.\run_local.ps1 test      # Run tests
.\run_local.ps1 lint      # Run ruff linter
.\run_local.ps1 format    # Format code
.\run_local.ps1 help      # Show help
```

### Linting & Formatting
```powershell
# Check code style
uv run ruff check backend/

# Auto-fix issues
uv run ruff check backend/ --fix

# Format code
uv run ruff format backend/
```

## 📊 Cosmos DB Document Examples

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
    "status": "in-progress",
    "dueDate": "2025-12-30T17:00:00Z"
  },
  "createdAt": "2025-12-27T10:00:00Z",
  "updatedAt": "2025-12-27T14:30:00Z"
}
```

## 🛣️ Roadmap

### ✅ Phase 1 (MVP - Current)
- [x] FastMCP server with Cosmos DB
- [x] Schema management tools
- [x] Entity CRUD tools
- [x] Schema validation
- [x] Dev-mode authentication
- [x] Local runner script

### 🔜 Phase 2 (Planned)
- [ ] Scalekit OAuth integration
- [ ] Multi-user support
- [ ] Relationships between entities
- [ ] Version history tracking
- [ ] Recurring task generation
- [ ] Advanced analytics tools
- [ ] Query DSL for complex filters

### 🔮 Phase 3 (Future)
- [ ] Dynamic web UI
- [ ] Real-time updates (WebSocket)
- [ ] Mobile app considerations
- [ ] Collaboration features
- [ ] AI-powered insights

## 📖 Documentation

- [Implementation Plan](https://github.com/user/repo/wiki/Implementation-Plan) _(if applicable)_
- [API Reference](https://github.com/user/repo/wiki/API-Reference) _(if applicable)_

## 🤝 Contributing

This project follows the [AI-Native Engineering principles](../enterprise_architecture/ai-engineering/principles.md) from the enterprise_architecture repository.

## 📄 License

MIT License - See LICENSE file for details

---

**Built with AI-Native Engineering** - 99% of code written by Claude using the productivity system it manages.
