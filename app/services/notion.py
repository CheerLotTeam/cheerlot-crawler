import httpx

from app.config import settings

NOTION_API_URL = "https://api.notion.com/v1"


def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def query_database(database_id: str) -> dict:
    response = httpx.post(
        f"{NOTION_API_URL}/databases/{database_id}/query",
        headers=_get_headers(),
        json={},
    )
    response.raise_for_status()
    return response.json()
