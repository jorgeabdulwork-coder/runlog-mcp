"""Run storage. In-memory for now; replaced by Cosmos DB in Phase 3."""


class InMemoryRunStore:
    def __init__(self) -> None:
        self._runs: list[dict] = []

    def add(self, run: dict) -> dict:
        self._runs.append(run)
        return run

    def list_for_user(self, user_id: str) -> list[dict]:
        return [run for run in self._runs if run["userId"] == user_id]