# Tests - Testing Strategy & Execution

**Source of truth for testing approach, test categories, running tests, and coverage goals.**

---

## Overview

The Productivity MCP Server follows a pragmatic testing approach balancing:

- **Integration Tests**: Real Cosmos DB testing for critical paths
- **Unit Tests**: Fast, isolated tests for business logic (future)
- **MCP Tool Tests**: End-to-end tests of MCP protocol (future)
- **Manual Testing**: Claude Desktop integration tests

**Current State:** Basic pytest setup with comprehensive integration tests in `scripts/test_local.py`. Sample data seeding available for manual testing.

**Philosophy:** Test critical paths, edge cases, and error handling. Don't aim for 100% coverage blindly—focus on meaningful tests that verify the schema-flexible, AI-driven architecture works correctly.

---

## Directory Structure

```
tests/
├── __init__.py                    # Test package initialization
├── fixtures/
│   └── sample_schemas.json        # Reusable schema definitions (task, goal, habit)
└── README.md                      # This file (testing strategy)
```

**Future structure:**
```
tests/
├── unit/                          # Fast, isolated tests
│   ├── test_schema_service.py     # Schema validation logic
│   ├── test_entity_service.py     # Entity management operations
│   └── test_validators.py         # Custom validation rules
├── integration/                   # Cosmos DB integration tests
│   ├── test_cosmos_operations.py  # CRUD operations
│   └── test_queries.py            # Filtering, sorting, pagination
├── mcp/                           # MCP protocol tests
│   ├── test_schema_tools.py       # Schema management tools
│   └── test_entity_tools.py       # Entity management tools
└── fixtures/                      # Shared test data
    ├── sample_schemas.json        # Entity type schemas
    └── sample_entities.json       # Sample entity instances
```

---

## Test Categories

### 1. Integration Tests (Current)

**Location:** `scripts/test_local.py`

**Purpose:** Verify the entire system works end-to-end against a real Cosmos DB instance

**What it tests:**
- **Schema operations:** Create, read, update, delete entity types
- **Entity operations:** Create, read, update, list, delete entities
- **Validation logic:** Required fields, enum values, type checking, default values
- **Multi-entity workflows:** Tasks, goals, habits with realistic data

**Why integration-first:**

This project uses schema-flexible, AI-driven data models with Cosmos DB. The value is in the system working together (services → validation → Cosmos DB → MCP tools), not isolated components. Integration tests verify the complete workflow.

**Run integration tests:**
```powershell
# Via run script (recommended)
.\run_local.ps1 test-local

# Or directly
.\.venv\Scripts\python.exe scripts\test_local.py
```

**Prerequisites:**
1. Cosmos DB initialized: `.\run_local.ps1 init`
2. `.env` file configured with Cosmos DB credentials
3. Virtual environment activated

**Example test scenarios:**
- Create task schema with required fields, enum values, defaults
- Create 3 tasks with different statuses (todo, in-progress, done)
- Update task status and verify version increments
- List tasks with filters (status="todo")
- Test validation failures (missing required field, invalid enum)

---

### 2. Unit Tests (Future - Phase 2)

**Purpose:** Test business logic in isolation without external dependencies

**Planned test files:**
- `tests/unit/test_schema_service.py` - Schema validation logic
- `tests/unit/test_entity_service.py` - Entity management operations
- `tests/unit/test_validators.py` - Custom validation rules
- `tests/unit/test_utils.py` - Utility functions

**Characteristics:**
- No Cosmos DB calls (use mocks)
- No network I/O
- Fast execution (< 100ms per test)
- High coverage of edge cases

**Example test structure:**
```python
# tests/unit/test_schema_validator.py
import pytest
from backend.services import schema_service

def test_validate_required_field_missing():
    """Test that missing required fields are detected."""
    schema = {
        "title": {"type": "string", "required": True}
    }
    data = {}  # Missing required 'title'

    with pytest.raises(ValueError, match="title"):
        schema_service.validate_entity_data(data, schema)

def test_validate_enum_invalid_value():
    """Test that invalid enum values are rejected."""
    schema = {
        "status": {
            "type": "enum",
            "enum_values": ["todo", "done"]
        }
    }
    data = {"status": "invalid"}

    with pytest.raises(ValueError, match="status.*invalid"):
        schema_service.validate_entity_data(data, schema)
```

**Run unit tests:**
```powershell
pytest tests/unit/ -v
```

---

### 3. MCP Tool Tests (Future - Phase 2)

**Purpose:** Test MCP tools end-to-end via the FastMCP server

**Planned test files:**
- `tests/mcp/test_schema_tools.py` - Schema management tools
- `tests/mcp/test_entity_tools.py` - Entity management tools
- `tests/mcp/test_mcp_integration.py` - Full MCP protocol compliance

**What to test:**
- MCP tool parameter validation
- Tool output format (success/error responses)
- Error handling and user-facing messages
- Authentication (when enabled)
- Scope validation (when enabled)

**Approach:**
- Mock FastMCP context
- Test tools directly (not via HTTP)
- Verify Cosmos DB interactions
- Check response structure

**Example test structure:**
```python
# tests/mcp/test_entity_tools.py
from backend.tools.entity_tools import create_entity_tool

def test_create_entity_success():
    """Test successful entity creation via MCP tool."""
    result = create_entity_tool(
        entity_type="task",
        data={"title": "Test Task"},
        metadata=None
    )

    assert result["success"] is True
    assert "entity_id" in result
    assert result["entity"]["data"]["title"] == "Test Task"

def test_create_entity_invalid_schema():
    """Test that invalid data returns user-friendly error."""
    result = create_entity_tool(
        entity_type="task",
        data={},  # Missing required 'title'
        metadata=None
    )

    assert result["success"] is False
    assert "error" in result
    assert "title" in result["error"].lower()
```

**Run MCP tool tests:**
```powershell
pytest tests/mcp/ -v
```

---

### 4. Manual Testing (Claude Desktop)

**Purpose:** Test real-world usage with Claude Desktop integration

**Process:**
1. Start MCP server: `.\run_local.ps1 mcp`
2. Configure Claude Desktop to connect to `http://localhost:8000`
3. Test natural language workflows:
   - "Create a task management system"
   - "Add a task: Review Q4 metrics, due Friday, high priority"
   - "Show me all my tasks"
   - "Mark the review task as done"
   - "What tasks are still pending?"

**Validation:**
- Claude successfully interprets natural language
- MCP tools are called with correct parameters
- Entities are created/updated in Cosmos DB
- No errors in Claude's responses
- Data persists and can be retrieved

**Alternative:** Use curl-based testing script
```powershell
# Start server in one terminal
.\run_local.ps1 mcp

# In another terminal, test with curl
.\run_local.ps1 test-mcp
```

---

## Running Tests

### All Tests (Pytest Suite)

```powershell
# Run all pytest tests (when implemented)
.\run_local.ps1 test

# Or directly
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

**What it runs:**
- All test files in `tests/` directory matching `test_*.py`
- Verbose output with test names and results

---

### Integration Tests (Current)

```powershell
# Run comprehensive integration tests
.\run_local.ps1 test-local

# Or directly
.\.venv\Scripts\python.exe scripts\test_local.py
```

**Test output:**
```
TEST 1: Schema Operations
  [OK] Created task schema (version 1)
  [OK] User has 1 entity types

TEST 2: Entity Operations
  [OK] Created: abc123 - Test task 1
  [OK] Retrieved: Test task 1
  [OK] Updated status to: done
  [OK] Found 3 tasks

TEST 3: Schema Validation
  [OK] Correctly rejected: ValueError
  [OK] Created with default status: todo

[OK] ALL TESTS PASSED!
```

---

### MCP Server Tests

```powershell
# Start MCP server (Terminal 1)
.\run_local.ps1 mcp

# Test with curl (Terminal 2)
.\run_local.ps1 test-mcp
```

**Tests:**
- Server startup and health
- Tool discovery (list available tools)
- Tool invocation (create entity, list entities)
- Error handling (invalid parameters)

---

### Test Options

```powershell
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run specific test file
pytest tests/unit/test_schema_service.py -v

# Run specific test function
pytest tests/unit/test_schema_service.py::test_validate_required_field -v

# Coverage report
pytest --cov=backend --cov-report=html
```

---

## Test Data

### Seed Data

**Purpose:** Populate database with realistic sample data for manual testing and development

**Run seed script:**
```powershell
.\run_local.ps1 seed
```

**What it creates:**

1. **Entity Type Schemas** (from `tests/fixtures/sample_schemas.json`):
   - `task`: title, status, priority, dueDate, tags
   - `goal`: title, targetDate, status, milestones, progress
   - `habit`: name, frequency, streak, lastCompleted, active

2. **Sample Entities**:
   - **5 Tasks**: Various statuses (todo, in-progress, done), priorities (low to urgent)
   - **3 Goals**: With milestones, progress tracking, target dates
   - **4 Habits**: Different frequencies (daily, weekly, monthly), active streaks

**Seed data details:**

**Tasks:**
- "Review Q4 performance metrics" (in-progress, high, due in 3 days)
- "Update project documentation" (todo, medium, due in 7 days)
- "Set up CI/CD pipeline" (todo, urgent, due tomorrow)
- "Code review for pull request #42" (done, medium)
- "Write blog post about AI-native engineering" (todo, low, due in 2 weeks)

**Goals:**
- "Ship productivity MVP by end of Q1 2025" (4 milestones, 25% progress)
- "Learn advanced Cosmos DB patterns" (3 milestones, 33% progress)
- "Contribute to open source weekly" (10% progress)

**Habits:**
- "Morning meditation" (daily, 21-day streak)
- "Weekly code review" (weekly, 8-week streak)
- "Monthly retrospective" (monthly, 3-month streak)
- "Daily standup notes" (daily, 45-day streak)

**Use cases:**
- Manual testing in Claude Desktop
- Demo data for presentations
- Development environment setup
- Learning how the system works

**Output:**
```
Seeding Productivity System with Sample Data
Creating entity type schemas...
  [OK] Created 'task' schema
  [OK] Created 'goal' schema
  [OK] Created 'habit' schema

Seeding tasks...
  [OK] Created task: Review Q4 performance metrics... [in-progress]

Total tasks: 5
Total goals: 3
Total habits: 4
[OK] Sample data seeded successfully!
```

---

### Test Fixtures

**Location:** `tests/fixtures/`

**Current fixtures:**
- `sample_schemas.json` - Entity type schema definitions (task, goal, habit)

**Usage in tests:**
```python
import json
from pathlib import Path

def load_fixture(filename):
    """Load a JSON fixture file."""
    path = Path(__file__).parent / "fixtures" / filename
    with open(path) as f:
        return json.load(f)

# In tests
schemas = load_fixture("sample_schemas.json")
task_schema = schemas["task"]
```

**Future fixtures (planned):**
- `sample_entities.json` - Sample entity instances
- `invalid_data.json` - Invalid data for error testing
- `edge_cases.json` - Edge case data (empty arrays, nulls, etc.)

---

## Test Coverage

### Current Coverage

**Status:** Basic integration tests only (~30% estimated)

**Priority areas:**
1. Schema validation logic (critical)
2. Entity CRUD operations (high)
3. Error handling (high)
4. Edge cases (medium)

---

### Coverage Targets

**Phase 1 (MVP - Current):**
- Integration tests: Comprehensive workflows
- Critical paths: 50%+
- Overall: Not measured yet

**Phase 2 (Q1 2025):**
- Unit tests implemented
- Critical paths: 80%+
- Error handling: 70%+
- Overall: 60%+

**Phase 3 (Q2 2025):**
- MCP tool tests implemented
- Critical paths: 90%+
- Overall: 75%+

**Philosophy:**
- Focus on meaningful coverage, not 100%
- Test critical business logic thoroughly
- Test error conditions and edge cases
- Integration points need high coverage
- Don't test trivial getters/setters

---

### Measuring Coverage

**Generate coverage report:**
```powershell
# Install pytest-cov (if not already)
pip install pytest-cov

# Run tests with coverage
pytest --cov=backend --cov-report=html

# View HTML report
start htmlcov/index.html
```

**Coverage report includes:**
- Overall coverage percentage
- Per-module coverage breakdown
- Line-by-line coverage (green = covered, red = not covered)
- Missing lines highlighted

**Exclude from coverage:**
- `__init__.py` files
- Test files themselves
- Development utilities
- Scripts (unless they contain business logic)

---

## CI/CD Integration

**Status:** Not yet implemented (planned for Phase 3)

**Planned GitHub Actions workflow:**
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run linter
        run: uv run ruff check backend/ scripts/
      - name: Run tests
        run: uv run pytest tests/ --cov=backend --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**Triggers:**
- On every push to `main` branch
- On every pull request

**Quality gates:**
- Linting must pass (ruff)
- All tests must pass (pytest)
- Coverage must not decrease
- No blocking issues found

**Integration with Azure Cosmos DB:**
- Use dedicated test Cosmos DB instance
- Configure credentials via GitHub Secrets
- Clean up test data after runs

---

## Writing New Tests

### Test Structure Template

```python
"""
Test module for [component being tested].
Tests cover [brief description of what's tested].
"""

import pytest
from backend.services import schema_service, entity_service
from backend.config import Config

USER_ID = Config.DEFAULT_USER_ID


class TestSchemaService:
    """Tests for schema service operations."""

    def test_create_entity_type_success(self):
        """Test successful entity type creation with valid schema."""
        # Arrange
        entity_type = "test_entity"
        schema_def = {
            "title": {"type": "string", "required": True},
            "status": {"type": "enum", "enum_values": ["active", "done"]}
        }

        # Act
        schema = schema_service.create_entity_type(
            user_id=USER_ID,
            entity_type_name=entity_type,
            schema_definition=schema_def
        )

        # Assert
        assert schema.version == 1
        assert entity_type in schema.entity_types
        assert "title" in schema.entity_types[entity_type].schema

        # Cleanup (if needed)
        schema_service.delete_entity_type(USER_ID, entity_type)

    def test_create_duplicate_entity_type_fails(self):
        """Test that creating duplicate entity types raises ValueError."""
        entity_type = "duplicate_test"
        schema_def = {"field": {"type": "string"}}

        # Create first time
        schema_service.create_entity_type(USER_ID, entity_type, schema_def)

        # Attempt duplicate creation
        with pytest.raises(ValueError, match="already exists"):
            schema_service.create_entity_type(USER_ID, entity_type, schema_def)

        # Cleanup
        schema_service.delete_entity_type(USER_ID, entity_type)
```

---

### Naming Conventions

**Test files:**
- `test_*.py` or `*_test.py`
- Match the module being tested: `test_schema_service.py` for `schema_service.py`

**Test classes:**
- `Test<ComponentName>`: e.g., `TestSchemaService`, `TestEntityService`
- Optional, but useful for grouping related tests

**Test functions:**
- `test_<what_it_tests>`: e.g., `test_create_entity_success`
- Be descriptive: `test_create_entity_missing_required_field_returns_error`
- Use underscores for readability

**Test docstrings:**
- One-line summary of what is tested
- Include expected behavior

---

### Best Practices

1. **Test isolation**: Each test should be independent and not rely on other tests
2. **Use AAA pattern**: Arrange (setup), Act (execute), Assert (verify)
3. **Test one thing**: Each test should verify one specific behavior
4. **Use fixtures**: Share common setup across tests with pytest fixtures
5. **Clean up**: Delete test data after tests complete
6. **Test errors**: Test both success and failure paths
7. **Edge cases**: Test boundaries, empty values, nulls
8. **Clear assertions**: Use specific assertions with helpful error messages

---

## Troubleshooting

### Common Issues

**1. Cosmos DB connection failed**

**Error:** `CosmosDBError: Unable to connect to Cosmos DB`

**Solution:**
```powershell
# Verify .env file exists and has correct credentials
cat .env

# Test connection
.\run_local.ps1 init

# Check firewall rules in Azure Portal (allow local IP)
```

---

**2. Tests fail with "Entity type not found"**

**Cause:** Schema not created before entity operations

**Solution:**
```powershell
# Create schemas first
.\run_local.ps1 seed  # Creates schemas + sample data

# Or in tests, create schema in setup
```

---

**3. Seed data already exists**

**Behavior:** Seed script skips existing schemas but creates new entities

**To reset database:**
```powershell
# WARNING: Deletes all data
.\run_local.ps1 init
```

---

**4. Import errors in tests**

**Error:** `ModuleNotFoundError: No module named 'backend'`

**Solution:**
```powershell
# Ensure PYTHONPATH includes backend/
$env:PYTHONPATH = "C:\projects\productivity\backend"

# Or use run_local.ps1 which sets this automatically
.\run_local.ps1 test
```

---

**5. Tests hang or timeout**

**Possible causes:**
- Cosmos DB connection issues
- Network latency
- Firewall blocking requests

**Solution:**
```powershell
# Test Cosmos DB connection directly
.\run_local.ps1 test-local

# Check Azure Portal for Cosmos DB status
# Verify network connectivity
```

---

**6. MCP tool tests fail**

**Error:** `Connection refused` or `Server not running`

**Cause:** MCP server not started

**Solution:**
```powershell
# Terminal 1: Start MCP server
.\run_local.ps1 mcp

# Terminal 2: Run MCP tests
pytest tests/mcp/ -v
```

---

## Related Documentation

- **Root README**: [../README.md](../README.md) - Project overview and quick start
- **Backend README**: [../backend/README.md](../backend/README.md) - Architecture and code structure
- **Scripts README**: [../scripts/README.md](../scripts/README.md) - Infrastructure and utility scripts
- **Enterprise Alignment Plan**: [../ENTERPRISE_ALIGNMENT_PLAN.md](../ENTERPRISE_ALIGNMENT_PLAN.md) - Documentation strategy

**Agent Instructions**: [../CLAUDE.md](../CLAUDE.md) - Multi-agent workflow rules

---

## Contributing

When adding new tests:

1. **Follow the structure**: Match existing test patterns and naming conventions
2. **Update this README**: Document new test categories, fixtures, or special setup
3. **Consider coverage**: Aim for meaningful coverage, not just high numbers
4. **Test edge cases**: Don't just test the happy path
5. **Keep tests fast**: Use mocks for unit tests, real DB for integration tests
6. **Clean up resources**: Delete test data after completion
7. **Document tricky tests**: Add comments explaining complex test scenarios

**Test review checklist:**
- [ ] All tests pass locally (`.\run_local.ps1 test`)
- [ ] Test names are descriptive
- [ ] Tests are isolated (don't depend on each other)
- [ ] Error cases are tested
- [ ] Edge cases are covered
- [ ] Test data is cleaned up
- [ ] README updated if needed

---

**Current Status**: Basic pytest setup, comprehensive integration tests in `scripts/test_local.py`

**Next Milestone**: Implement unit tests for services (Phase 2, Q1 2025)

**Coverage Target**: 60%+ by end of Phase 2

**Owner**: Development Team

**Last Updated**: 2025-12-27 (Phase 1: Enterprise Alignment)
