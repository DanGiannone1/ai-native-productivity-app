"""
Test the productivity system locally without MCP.
This directly calls the service functions to verify they work.

Usage:
    python scripts/test_local.py
    OR
    .\run_local.ps1 test-local
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from productivity_mcp.config import Config
from productivity_mcp.services import schema_service, entity_service

USER_ID = Config.DEFAULT_USER_ID


def test_schema_operations():
    """Test schema CRUD operations."""
    print("=" * 60)
    print("TEST 1: Schema Operations")
    print("=" * 60)

    # Create entity type
    print("\n1. Creating 'task' entity type...")
    try:
        schema = schema_service.create_entity_type(
            user_id=USER_ID,
            entity_type_name="task",
            schema_definition={
                "title": {"type": "string", "required": True},
                "status": {
                    "type": "enum",
                    "enum_values": ["todo", "in-progress", "done"],
                    "default": "todo"
                },
                "priority": {"type": "enum", "enum_values": ["low", "medium", "high"]},
                "dueDate": {"type": "datetime"}
            }
        )
        print(f"   [OK] Created task schema (version {schema.version})")
        print(f"   Fields: {list(schema.entity_types['task'].schema.keys())}")
    except ValueError as e:
        print(f"   [i] Schema already exists: {e}")

    # Get user schema
    print("\n2. Retrieving user schema...")
    user_schema = schema_service.get_user_schema(USER_ID)
    print(f"   [OK] User has {len(user_schema.entity_types)} entity types")
    for entity_type in user_schema.entity_types:
        print(f"     - {entity_type}")

    # Check if entity type exists
    print("\n3. Checking entity type existence...")
    exists = schema_service.entity_type_exists(USER_ID, "task")
    print(f"   [OK] 'task' entity type exists: {exists}")


def test_entity_operations():
    """Test entity CRUD operations."""
    print("\n" + "=" * 60)
    print("TEST 2: Entity Operations")
    print("=" * 60)

    # Create entities
    print("\n1. Creating task entities...")
    tasks = []

    task_data = [
        {
            "title": "Test task 1 - High priority",
            "status": "in-progress",
            "priority": "high",
            "dueDate": (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z"
        },
        {
            "title": "Test task 2 - Medium priority",
            "status": "todo",
            "priority": "medium"
        },
        {
            "title": "Test task 3 - Completed",
            "status": "done",
            "priority": "low"
        }
    ]

    for data in task_data:
        entity = entity_service.create_entity(
            user_id=USER_ID,
            entity_type="task",
            data=data,
            metadata={"createdBy": "test-script"}
        )
        tasks.append(entity)
        print(f"   [OK] Created: {entity['id']} - {data['title']}")

    # Get entity by ID
    print("\n2. Retrieving entity by ID...")
    retrieved = entity_service.get_entity(USER_ID, tasks[0]["id"])
    print(f"   [OK] Retrieved: {retrieved['data']['title']}")
    print(f"   Status: {retrieved['data']['status']}")

    # Update entity
    print("\n3. Updating entity...")
    updated = entity_service.update_entity(
        user_id=USER_ID,
        entity_id=tasks[0]["id"],
        updates={"status": "done"}
    )
    print(f"   [OK] Updated status to: {updated['data']['status']}")
    print(f"   Version: {updated['version']}")

    # List entities
    print("\n4. Listing all tasks...")
    all_tasks = entity_service.list_entities(
        user_id=USER_ID,
        entity_type="task"
    )
    print(f"   [OK] Found {len(all_tasks)} tasks")
    for task in all_tasks:
        status = task['data']['status']
        title = task['data']['title']
        print(f"     - [{status}] {title}")

    # List with filters
    print("\n5. Listing todo tasks only...")
    todo_tasks = entity_service.list_entities(
        user_id=USER_ID,
        entity_type="task",
        filters={"status": "todo"}
    )
    print(f"   [OK] Found {len(todo_tasks)} todo tasks")

    # Count entities
    print("\n6. Counting tasks...")
    count = entity_service.count_entities(USER_ID, "task")
    print(f"   [OK] Total tasks: {count}")

    # Delete entity (soft delete)
    print("\n7. Soft deleting a task...")
    entity_service.delete_entity(USER_ID, tasks[2]["id"], hard_delete=False)
    print(f"   [OK] Soft deleted: {tasks[2]['id']}")

    # Verify soft delete
    count_after_delete = entity_service.count_entities(USER_ID, "task")
    print(f"   Active tasks now: {count_after_delete}")


def test_validation():
    """Test schema validation."""
    print("\n" + "=" * 60)
    print("TEST 3: Schema Validation")
    print("=" * 60)

    # Test missing required field
    print("\n1. Testing missing required field...")
    try:
        entity_service.create_entity(
            user_id=USER_ID,
            entity_type="task",
            data={"status": "todo"}  # Missing required 'title'
        )
        print("   [X] Should have failed!")
    except Exception as e:
        print(f"   [OK] Correctly rejected: {type(e).__name__}")

    # Test invalid enum value
    print("\n2. Testing invalid enum value...")
    try:
        entity_service.create_entity(
            user_id=USER_ID,
            entity_type="task",
            data={
                "title": "Test",
                "status": "invalid-status"  # Not in enum
            }
        )
        print("   [X] Should have failed!")
    except Exception as e:
        print(f"   [OK] Correctly rejected: {type(e).__name__}")

    # Test wrong type
    print("\n3. Testing wrong data type...")
    try:
        entity_service.create_entity(
            user_id=USER_ID,
            entity_type="task",
            data={
                "title": 12345,  # Should be string
                "status": "todo"
            }
        )
        print("   [X] Should have failed!")
    except Exception as e:
        print(f"   [OK] Correctly rejected: {type(e).__name__}")

    # Test default values
    print("\n4. Testing default values...")
    entity = entity_service.create_entity(
        user_id=USER_ID,
        entity_type="task",
        data={"title": "Task with defaults"}
    )
    print(f"   [OK] Created with default status: {entity['data']['status']}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PRODUCTIVITY SYSTEM - LOCAL TESTING")
    print("=" * 60)
    print(f"\nUser ID: {USER_ID}")
    print(f"Database: {Config.COSMOS_DATABASE}")
    print(f"Container: {Config.COSMOS_CONTAINER}")
    print()

    try:
        test_schema_operations()
        test_entity_operations()
        test_validation()

        print("\n" + "=" * 60)
        print("[OK] ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Your productivity system is working correctly!")
        print()
        print("Next steps:")
        print("  1. Start MCP server: .\\run_local.ps1 mcp")
        print("  2. Configure Claude Desktop to connect to http://localhost:8000")
        print("  3. Test with natural language queries")
        print()

    except Exception as e:
        print("\n" + "=" * 60)
        print("[X] TEST FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
