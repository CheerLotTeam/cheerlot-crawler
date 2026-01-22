from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.infrastructure.notion import NotionClient
from app.infrastructure.notion.mappers import BaseMapper

T = TypeVar("T", bound=BaseModel)

class BaseRepository(ABC, Generic[T]):

    def __init__(
        self,
        client: NotionClient | None = None,
        mapper: BaseMapper[T] | None = None,
    ):
        self._client = client or NotionClient()
        self._mapper = mapper or self._create_mapper()

    @property
    @abstractmethod
    def database_id(self) -> str:
        pass

    @abstractmethod
    def _create_mapper(self) -> BaseMapper[T]:
        pass

    def find_all(self) -> list[T]:
        pages = self._client.query_database(self.database_id)
        return [self._mapper.to_model(page) for page in pages]

    def find_by_filter(self, filter: dict) -> list[T]:
        pages = self._client.query_database(self.database_id, filter=filter)
        return [self._mapper.to_model(page) for page in pages]

    def create(self, model: T) -> dict:
        properties = self._mapper.to_properties(model)
        return self._client.create_page(self.database_id, properties)

    def update(self, page_id: str, model: T) -> dict:
        properties = self._mapper.to_properties(model)
        return self._client.update_page(page_id, properties)

    def delete(self, page_id: str) -> dict:
        return self._client.archive_page(page_id)
    