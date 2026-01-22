from app.config import settings
from app.models import CheerSong
from app.repositories.base import BaseRepository
from app.infrastructure.notion.mappers import BaseMapper, CheerSongMapper

class CheerSongRepository(BaseRepository[CheerSong]):

    @property
    def database_id(self) -> str:
        return settings.notion_cheersong_db_id

    def _create_mapper(self) -> BaseMapper[CheerSong]:
        return CheerSongMapper()

    def find_by_player_code(self, player_code: str) -> list[CheerSong]:
        filter = {
            "property": CheerSongMapper.PROP_PLAYER_CODE,
            "title": {"equals": player_code},
        }
        return self.find_by_filter(filter)
