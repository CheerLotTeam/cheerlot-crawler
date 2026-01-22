from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class BaseMapper(ABC, Generic[T]):

    @abstractmethod
    def to_properties(self, model: T) -> dict:
        """Pydantic 모델 -> Notion 속성"""
        pass

    @abstractmethod
    def to_model(self, page: dict) -> T:
        """Notion 페이지 -> Pydantic 모델"""
        pass

    # === Notion 속성 읽기 헬퍼 ===

    def _get_title(self, properties: dict, key: str) -> str:
        title_array = properties.get(key, {}).get("title", [])
        return title_array[0]["plain_text"] if title_array else ""

    def _get_rich_text(self, properties: dict, key: str) -> str:
        rich_text_array = properties.get(key, {}).get("rich_text", [])
        return rich_text_array[0]["plain_text"] if rich_text_array else ""

    def _get_number(self, properties: dict, key: str) -> int | None:
        return properties.get(key, {}).get("number")

    def _get_checkbox(self, properties: dict, key: str) -> bool:
        return properties.get(key, {}).get("checkbox", False)

    def _get_date(self, properties: dict, key: str) -> str | None:
        date_obj = properties.get(key, {}).get("date")
        return date_obj.get("start") if date_obj else None

    # === Notion 속성 쓰기 헬퍼 ===

    def _make_title(self, value: str) -> dict:
        return {"title": [{"text": {"content": value}}]}

    def _make_rich_text(self, value: str) -> dict:
        return {"rich_text": [{"text": {"content": value}}]}

    def _make_number(self, value: int | None) -> dict:
        return {"number": value}

    def _make_checkbox(self, value: bool) -> dict:
        return {"checkbox": value}

    def _make_date(self, value: str | None) -> dict:
        return {"date": {"start": value} if value else None}
