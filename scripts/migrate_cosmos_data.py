"""
Migrate data from old Cosmos DB account to new serverless account.

Usage:
    python scripts/migrate_cosmos_data.py --old-account cosmos-prism-dev --new-account cosmos-prism-dev-serverless --resource-group prism-dev
"""

import argparse
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError


def get_cosmos_client(account_name: str, resource_group: str):
    """Get Cosmos client for specified account."""
    import subprocess

    # Get connection info from Azure CLI
    host = subprocess.check_output([
        "az", "cosmosdb", "show",
        "--name", account_name,
        "--resource-group", resource_group,
        "--query", "documentEndpoint",
        "--output", "tsv"
    ]).decode().strip()

    key = subprocess.check_output([
        "az", "cosmosdb", "keys", "list",
        "--name", account_name,
        "--resource-group", resource_group,
        "--query", "primaryMasterKey",
        "--output", "tsv"
    ]).decode().strip()

    return CosmosClient(host, key)


def migrate_data(old_client, new_client, database_name: str, container_name: str):
    """Copy all data from old container to new container."""

    print(f"  Connecting to old database: {database_name}")
    old_database = old_client.get_database_client(database_name)
    old_container = old_database.get_container_client(container_name)

    print(f"  Connecting to new database: {database_name}")
    new_database = new_client.get_database_client(database_name)
    new_container = new_database.get_container_client(container_name)

    # Query all items from old container
    print(f"  Reading all items from old container...")
    items = list(old_container.read_all_items())

    print(f"  Found {len(items)} items to migrate")

    if len(items) == 0:
        print(f"  [i] No data to migrate")
        return 0

    # Copy items to new container
    migrated = 0
    errors = 0

    for item in items:
        try:
            # Upsert to new container
            new_container.upsert_item(item)
            migrated += 1

            if migrated % 10 == 0:
                print(f"    Migrated {migrated}/{len(items)} items...")

        except Exception as e:
            print(f"    [X] Failed to migrate item {item.get('id')}: {e}")
            errors += 1

    print(f"  [OK] Migrated {migrated} items ({errors} errors)")
    return migrated


def main():
    parser = argparse.ArgumentParser(description="Migrate Cosmos DB data to serverless account")
    parser.add_argument("--old-account", required=True, help="Old Cosmos DB account name")
    parser.add_argument("--new-account", required=True, help="New serverless account name")
    parser.add_argument("--resource-group", required=True, help="Resource group")
    parser.add_argument("--database", default="productivity", help="Database name")
    parser.add_argument("--container", default="productivity-data", help="Container name")

    args = parser.parse_args()

    print("=" * 60)
    print("Cosmos DB Data Migration")
    print("=" * 60)
    print()
    print(f"Old account: {args.old_account}")
    print(f"New account: {args.new_account}")
    print(f"Database: {args.database}")
    print(f"Container: {args.container}")
    print()

    try:
        # Connect to both accounts
        print("Connecting to Cosmos DB accounts...")
        old_client = get_cosmos_client(args.old_account, args.resource_group)
        new_client = get_cosmos_client(args.new_account, args.resource_group)
        print("  [OK] Connected to both accounts")
        print()

        # Migrate data
        total_migrated = migrate_data(
            old_client,
            new_client,
            args.database,
            args.container
        )

        print()
        print("=" * 60)
        print("[OK] Migration complete!")
        print("=" * 60)
        print(f"Total items migrated: {total_migrated}")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print("[X] Migration failed!")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
