"""Run storage: in-memory (tests, quick local work) or Azure Cosmos DB."""
import os


class InMemoryRunStore:
    def __init__(self) -> None:
        self._runs: list[dict] = []

    def add(self, run: dict) -> dict:
        self._runs.append(run)
        return run

    def list_for_user(self, user_id: str) -> list[dict]:
        return [run for run in self._runs if run["userId"] == user_id]


class CosmosRunStore:
    def __init__(self, endpoint: str, database: str, container: str,
                 key: str | None = None, verify_ssl: bool = True,
                 create_if_missing: bool = False) -> None:
        from azure.cosmos import CosmosClient, PartitionKey

        if key:
            credential = key
        else:
            # In Azure: sign in with the Function App's managed identity (Phase 5)
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()

        client = CosmosClient(endpoint, credential=credential, connection_verify=verify_ssl)

        if create_if_missing:
            db = client.create_database_if_not_exists(id=database)
            self._container = db.create_container_if_not_exists(
                id=container, partition_key=PartitionKey(path="/userId")
            )
        else:
            self._container = client.get_database_client(database).get_container_client(container)

    @staticmethod
    def _clean(item: dict) -> dict:
        """Drop Cosmos system fields like _rid, _etag, and _ts."""
        return {key: value for key, value in item.items() if not key.startswith("_")}

    def add(self, run: dict) -> dict:
        self._container.create_item(body=run)
        return run

    def list_for_user(self, user_id: str) -> list[dict]:
        items = self._container.query_items(
            query="SELECT * FROM c WHERE c.userId = @userId",
            parameters=[{"name": "@userId", "value": user_id}],
            partition_key=user_id,
        )
        return [self._clean(item) for item in items]


def _is_true(value: str | None) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def create_store():
    """Pick the store based on app settings. Defaults to in-memory."""
    if os.environ.get("RUNLOG_STORE", "memory").lower() != "cosmos":
        return InMemoryRunStore()

    return CosmosRunStore(
        endpoint=os.environ["COSMOS_ENDPOINT"],
        database=os.environ.get("COSMOS_DATABASE", "runlog"),
        container=os.environ.get("COSMOS_CONTAINER", "runs"),
        key=os.environ.get("COSMOS_KEY"),
        verify_ssl=not os.environ.get("COSMOS_VERIFY_SSL") or _is_true(os.environ.get("COSMOS_VERIFY_SSL")),
        create_if_missing=_is_true(os.environ.get("COSMOS_CREATE_IF_MISSING")),
    )