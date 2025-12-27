"""
Cosmos DB client singleton for the productivity MCP server.
Adapted from enterprise_architecture template.
"""

from azure.cosmos import CosmosClient, ContainerProxy, DatabaseProxy, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError

from backend.config import Config
from backend.utils.errors import CosmosDBError

# Global singleton instances
_cosmos_client: CosmosClient | None = None
_database: DatabaseProxy | None = None
_container: ContainerProxy | None = None


def get_cosmos_client() -> CosmosClient:
    """
    Get or create the Cosmos DB client singleton.

    Returns:
        CosmosClient: The initialized Cosmos client

    Raises:
        CosmosDBError: If client initialization fails
    """
    global _cosmos_client

    if _cosmos_client is None:
        try:
            _cosmos_client = CosmosClient(
                url=Config.COSMOS_HOST,
                credential=Config.COSMOS_KEY,
            )
        except Exception as e:
            raise CosmosDBError(f"Failed to initialize Cosmos client: {str(e)}") from e

    return _cosmos_client


def get_database() -> DatabaseProxy:
    """
    Get or create the database proxy.

    Returns:
        DatabaseProxy: The database proxy

    Raises:
        CosmosDBError: If database access fails
    """
    global _database

    if _database is None:
        try:
            client = get_cosmos_client()
            _database = client.get_database_client(Config.COSMOS_DATABASE)
        except Exception as e:
            raise CosmosDBError(f"Failed to access database '{Config.COSMOS_DATABASE}': {str(e)}") from e

    return _database


def get_container() -> ContainerProxy:
    """
    Get or create the container proxy.

    Returns:
        ContainerProxy: The container proxy

    Raises:
        CosmosDBError: If container access fails
    """
    global _container

    if _container is None:
        try:
            database = get_database()
            _container = database.get_container_client(Config.COSMOS_CONTAINER)
        except Exception as e:
            raise CosmosDBError(f"Failed to access container '{Config.COSMOS_CONTAINER}': {str(e)}") from e

    return _container


def create_database_if_not_exists() -> DatabaseProxy:
    """
    Create the database if it doesn't exist.

    Returns:
        DatabaseProxy: The database proxy

    Raises:
        CosmosDBError: If database creation fails
    """
    try:
        client = get_cosmos_client()
        database = client.create_database_if_not_exists(id=Config.COSMOS_DATABASE)
        return database
    except Exception as e:
        raise CosmosDBError(f"Failed to create database '{Config.COSMOS_DATABASE}': {str(e)}") from e


def create_container_if_not_exists() -> ContainerProxy:
    """
    Create the container if it doesn't exist.

    Container is partitioned by /userId for efficient single-partition queries.

    Returns:
        ContainerProxy: The container proxy

    Raises:
        CosmosDBError: If container creation fails
    """
    try:
        database = create_database_if_not_exists()

        # Container partitioned by userId
        container = database.create_container_if_not_exists(
            id=Config.COSMOS_CONTAINER,
            partition_key=PartitionKey(path="/userId"),
            offer_throughput=400,  # Minimum RU/s for dev
        )

        print(f"✓ Container '{Config.COSMOS_CONTAINER}' ready (partitioned by /userId)")
        return container

    except Exception as e:
        raise CosmosDBError(f"Failed to create container '{Config.COSMOS_CONTAINER}': {str(e)}") from e


def query_items(
    query: str,
    parameters: list[dict] | None = None,
    partition_key: str | None = None,
    max_item_count: int = 100,
) -> list[dict]:
    """
    Execute a query against the container.

    Args:
        query: SQL query string
        parameters: Optional query parameters
        partition_key: Optional partition key for single-partition query
        max_item_count: Maximum items to return

    Returns:
        List of query results

    Raises:
        CosmosDBError: If query execution fails
    """
    try:
        container = get_container()

        query_kwargs = {
            "query": query,
            "enable_cross_partition_query": partition_key is None,
            "max_item_count": max_item_count,
        }

        if parameters:
            query_kwargs["parameters"] = parameters

        if partition_key:
            query_kwargs["partition_key"] = partition_key

        items = list(container.query_items(**query_kwargs))
        return items

    except CosmosHttpResponseError as e:
        raise CosmosDBError(f"Query failed: {e.message} (status {e.status_code})") from e
    except Exception as e:
        raise CosmosDBError(f"Query execution error: {str(e)}") from e


def create_item(item: dict) -> dict:
    """
    Create a new item in the container.

    Args:
        item: Document to create (must include 'userId' for partition key)

    Returns:
        Created item with metadata

    Raises:
        CosmosDBError: If item creation fails
    """
    try:
        container = get_container()

        if "userId" not in item:
            raise CosmosDBError("Item must include 'userId' field for partition key")

        created_item = container.create_item(body=item)
        return created_item

    except CosmosHttpResponseError as e:
        raise CosmosDBError(f"Failed to create item: {e.message} (status {e.status_code})") from e
    except Exception as e:
        raise CosmosDBError(f"Item creation error: {str(e)}") from e


def read_item(item_id: str, partition_key: str) -> dict:
    """
    Read an item by ID and partition key.

    Args:
        item_id: Document ID
        partition_key: Partition key value (userId)

    Returns:
        The item document

    Raises:
        CosmosResourceNotFoundError: If item not found
        CosmosDBError: If read fails
    """
    try:
        container = get_container()
        item = container.read_item(item=item_id, partition_key=partition_key)
        return item

    except CosmosResourceNotFoundError:
        raise
    except CosmosHttpResponseError as e:
        raise CosmosDBError(f"Failed to read item: {e.message} (status {e.status_code})") from e
    except Exception as e:
        raise CosmosDBError(f"Item read error: {str(e)}") from e


def upsert_item(item: dict) -> dict:
    """
    Create or update an item.

    Args:
        item: Document to upsert (must include 'id' and 'userId')

    Returns:
        Upserted item with metadata

    Raises:
        CosmosDBError: If upsert fails
    """
    try:
        container = get_container()

        if "userId" not in item:
            raise CosmosDBError("Item must include 'userId' field for partition key")
        if "id" not in item:
            raise CosmosDBError("Item must include 'id' field")

        upserted_item = container.upsert_item(body=item)
        return upserted_item

    except CosmosHttpResponseError as e:
        raise CosmosDBError(f"Failed to upsert item: {e.message} (status {e.status_code})") from e
    except Exception as e:
        raise CosmosDBError(f"Item upsert error: {str(e)}") from e


def delete_item(item_id: str, partition_key: str) -> None:
    """
    Delete an item by ID and partition key.

    Args:
        item_id: Document ID
        partition_key: Partition key value (userId)

    Raises:
        CosmosResourceNotFoundError: If item not found
        CosmosDBError: If deletion fails
    """
    try:
        container = get_container()
        container.delete_item(item=item_id, partition_key=partition_key)

    except CosmosResourceNotFoundError:
        raise
    except CosmosHttpResponseError as e:
        raise CosmosDBError(f"Failed to delete item: {e.message} (status {e.status_code})") from e
    except Exception as e:
        raise CosmosDBError(f"Item deletion error: {str(e)}") from e
