import httpx
from notion_client import Client
from notion_client.errors import APIResponseError

from app.config import settings


class NotionClientError(Exception):
    pass


class NotionClient:
    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.notion_api_key
        self._client = Client(auth=self._api_key)

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def query_database(
        self,
        database_id: str,
        filter: dict | None = None,
        sorts: list[dict] | None = None,
    ) -> list[dict]:
        try:
            body = {}
            if filter:
                body["filter"] = filter
            if sorts:
                body["sorts"] = sorts

            url = f"{self.BASE_URL}/databases/{database_id}/query"
            response = httpx.post(url, headers=self._get_headers(), json=body)
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPStatusError as e:
            raise NotionClientError(f"Database query failed: {e.response.text}") from e

    def create_page(self, database_id: str, properties: dict) -> dict:
        try:
            return self._client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
            )
        except APIResponseError as e:
            raise NotionClientError(f"Page create failed: {str(e)}") from e

    def update_page(self, page_id: str, properties: dict) -> dict:
        try:
            return self._client.pages.update(
                page_id=page_id,
                properties=properties,
            )
        except APIResponseError as e:
            raise NotionClientError(f"Page update failed: {str(e)}") from e

    def archive_page(self, page_id: str) -> dict:
        try:
            return self._client.pages.update(
                page_id=page_id,
                archived=True,
            )
        except APIResponseError as e:
            raise NotionClientError(f"Page archive failed: {str(e)}") from e
