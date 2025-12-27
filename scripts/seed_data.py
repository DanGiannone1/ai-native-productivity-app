"""
Seed sample data for testing the productivity MCP server.
Creates 3 entity types (task, goal, habit) and populates with sample entities.

Usage:
    python scripts/seed_data.py
    OR
    .\run_local.ps1 seed
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.config import Config
from backend.services import schema_service, entity_service
from backend.utils.errors import CosmosDBError, SchemaValidationError

# Sample user ID (from dev mode)
USER_ID = Config.DEFAULT_USER_ID


def load_sample_schemas():
    """Load sample schemas from fixtures."""
    fixtures_path = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_schemas.json"
    with open(fixtures_path) as f:
        return json.load(f)


def create_schemas():
    """Create entity type schemas."""
    print("Creating entity type schemas...")

    schemas = load_sample_schemas()

    for entity_type, schema_def in schemas.items():
        try:
            schema_service.create_entity_type(
                user_id=USER_ID,
                entity_type_name=entity_type,
                schema_definition=schema_def,
            )
            print(f"  [OK] Created '{entity_type}' schema")
        except ValueError:
            print(f"  [i] '{entity_type}' schema already exists, skipping")
        except SchemaValidationError as e:
            print(f"  [X] Failed to create '{entity_type}' schema: {e}")


def seed_tasks():
    """Create sample task entities."""
    print("\nSeeding tasks...")

    tasks = [
        {
            "title": "Review Q4 performance metrics",
            "description": "Analyze sales data and prepare presentation for leadership",
            "status": "in-progress",
            "priority": "high",
            "dueDate": (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z",
            "tags": ["work", "quarterly-review"],
        },
        {
            "title": "Update project documentation",
            "description": "Document new MCP tools and update README",
            "status": "todo",
            "priority": "medium",
            "dueDate": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
            "tags": ["documentation", "productivity"],
        },
        {
            "title": "Set up CI/CD pipeline",
            "description": "Configure GitHub Actions for automated testing and deployment",
            "status": "todo",
            "priority": "urgent",
            "dueDate": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "tags": ["devops", "infrastructure"],
        },
        {
            "title": "Code review for pull request #42",
            "description": "Review entity service refactoring",
            "status": "done",
            "priority": "medium",
            "tags": ["code-review", "completed"],
        },
        {
            "title": "Write blog post about AI-native engineering",
            "status": "todo",
            "priority": "low",
            "dueDate": (datetime.utcnow() + timedelta(days=14)).isoformat() + "Z",
            "tags": ["writing", "side-project"],
        },
    ]

    for task_data in tasks:
        try:
            entity = entity_service.create_entity(
                user_id=USER_ID,
                entity_type="task",
                data=task_data,
                metadata={"createdBy": "seed-script", "source": "sample-data"},
            )
            status = task_data["status"]
            print(f"  [OK] Created task: {task_data['title'][:50]}... [{status}]")
        except Exception as e:
            print(f"  [X] Failed to create task: {e}")


def seed_goals():
    """Create sample goal entities."""
    print("\nSeeding goals...")

    goals = [
        {
            "title": "Ship productivity MVP by end of Q1 2025",
            "description": "Complete and deploy the schema-flexible productivity system",
            "targetDate": "2025-03-31T00:00:00Z",
            "status": "active",
            "milestones": [
                {"title": "Complete backend implementation", "done": True},
                {"title": "Build dynamic UI", "done": False},
                {"title": "Deploy to production", "done": False},
                {"title": "Onboard first 10 users", "done": False},
            ],
            "progress": 25,
        },
        {
            "title": "Learn advanced Cosmos DB patterns",
            "description": "Master partition strategies, indexing, and change feed",
            "targetDate": "2025-02-28T00:00:00Z",
            "status": "active",
            "milestones": [
                {"title": "Complete official documentation", "done": True},
                {"title": "Build sample projects", "done": False},
                {"title": "Pass certification exam", "done": False},
            ],
            "progress": 33,
        },
        {
            "title": "Contribute to open source weekly",
            "description": "Make at least one meaningful contribution per week",
            "targetDate": "2025-12-31T00:00:00Z",
            "status": "active",
            "progress": 10,
        },
    ]

    for goal_data in goals:
        try:
            entity = entity_service.create_entity(
                user_id=USER_ID,
                entity_type="goal",
                data=goal_data,
                metadata={"createdBy": "seed-script"},
            )
            progress = goal_data.get("progress", 0)
            print(f"  [OK] Created goal: {goal_data['title'][:50]}... [{progress}% complete]")
        except Exception as e:
            print(f"  [X] Failed to create goal: {e}")


def seed_habits():
    """Create sample habit entities."""
    print("\nSeeding habits...")

    habits = [
        {
            "name": "Morning meditation",
            "description": "10 minutes of mindfulness meditation",
            "frequency": "daily",
            "streak": 21,
            "lastCompleted": datetime.utcnow().isoformat() + "Z",
            "active": True,
        },
        {
            "name": "Weekly code review",
            "description": "Review team's pull requests and provide feedback",
            "frequency": "weekly",
            "streak": 8,
            "lastCompleted": (datetime.utcnow() - timedelta(days=2)).isoformat() + "Z",
            "active": True,
        },
        {
            "name": "Monthly retrospective",
            "description": "Reflect on progress and set goals for next month",
            "frequency": "monthly",
            "streak": 3,
            "lastCompleted": (datetime.utcnow() - timedelta(days=15)).isoformat() + "Z",
            "active": True,
        },
        {
            "name": "Daily standup notes",
            "description": "Document key updates and blockers",
            "frequency": "daily",
            "streak": 45,
            "lastCompleted": datetime.utcnow().isoformat() + "Z",
            "active": True,
        },
    ]

    for habit_data in habits:
        try:
            entity = entity_service.create_entity(
                user_id=USER_ID,
                entity_type="habit",
                data=habit_data,
                metadata={"createdBy": "seed-script"},
            )
            streak = habit_data["streak"]
            print(f"  [OK] Created habit: {habit_data['name']} [{streak} day streak]")
        except Exception as e:
            print(f"  [X] Failed to create habit: {e}")


def print_summary():
    """Print summary of seeded data."""
    print("\n" + "=" * 60)
    print("Seeding Summary")
    print("=" * 60)

    try:
        task_count = entity_service.count_entities(USER_ID, "task")
        goal_count = entity_service.count_entities(USER_ID, "goal")
        habit_count = entity_service.count_entities(USER_ID, "habit")

        print(f"Total tasks: {task_count}")
        print(f"Total goals: {goal_count}")
        print(f"Total habits: {habit_count}")
        print(f"Total entities: {task_count + goal_count + habit_count}")
        print()
        print("[OK] Sample data seeded successfully!")
    except Exception as e:
        print(f"[X] Failed to get summary: {e}")


def main():
    """Main seeding workflow."""
    print("=" * 60)
    print("Seeding Productivity System with Sample Data")
    print("=" * 60)
    print()
    print(f"User ID: {USER_ID}")
    print(f"Database: {Config.COSMOS_DATABASE}")
    print(f"Container: {Config.COSMOS_CONTAINER}")
    print()

    try:
        # Create schemas
        create_schemas()

        # Seed entities
        seed_tasks()
        seed_goals()
        seed_habits()

        # Print summary
        print_summary()

        print()
        print("Next steps:")
        print("  1. Start MCP server: .\\run_local.ps1 mcp")
        print("  2. Connect Claude Desktop")
        print("  3. Try: list_entities('task')")
        print()

    except CosmosDBError as e:
        print()
        print("=" * 60)
        print("[X] Seeding failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Please ensure:")
        print("  - Cosmos DB is initialized (run .\\run_local.ps1 init)")
        print("  - .env file is configured correctly")
        sys.exit(1)

    except Exception as e:
        print()
        print("=" * 60)
        print("[X] Unexpected error!")
        print("=" * 60)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

