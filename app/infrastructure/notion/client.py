from notion_client import Client
from notion_client.errors import APIResponseError

from app.config import settings

class NotionClientError(Exception):
    pass

class NotionClient:

    def __init__(self, api_key: str | None = None):
        self._client = Client(auth=api_key or settings.notion_api_key)

    def query_database(
        self,
        database_id: str,
        filter: dict | None = None,
        sorts: list[dict] | None = None,
    ) -> list[dict]:
        try:
            response = self._client.databases.query(
                database_id=database_id,
                filter=filter,
                sorts=sorts,
            )
            return response.get("results", [])
        except APIResponseError as e:
            raise NotionClientError(f"Database query failed: {e.message}") from e

    def create_page(self, database_id: str, properties: dict) -> dict:
        try:
            return self._client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
            )
        except APIResponseError as e:
            raise NotionClientError(f"Page create failed: {e.message}") from e

    def update_page(self, page_id: str, properties: dict) -> dict:
        try:
            return self._client.pages.update(
                page_id=page_id,
                properties=properties,
            )
        except APIResponseError as e:
            raise NotionClientError(f"Page update failed: {e.message}") from e

    def archive_page(self, page_id: str) -> dict:
        try:
            return self._client.pages.update(
                page_id=page_id,
                archived=True,
            )
        except APIResponseError as e:
            raise NotionClientError(f"Page archive failed: {e.message}") from e
