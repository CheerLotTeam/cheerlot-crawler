from app.config import settings
from app.models import Player
from app.repositories.base import BaseRepository
from app.infrastructure.notion.mappers import BaseMapper, PlayerMapper

class PlayerRepository(BaseRepository[Player]):

    @property
    def database_id(self) -> str:
        return settings.notion_player_db_id

    def _create_mapper(self) -> BaseMapper[Player]:
        return PlayerMapper()

    def find_by_player_code(self, player_code: str) -> Player | None:
        filter = {
            "property": PlayerMapper.PROP_PLAYER_CODE,
            "title": {"equals": player_code},
        }
        results = self.find_by_filter(filter)
        return results[0] if results else None

    def find_by_team_code(self, team_code: str) -> list[Player]:
        filter = {
            "property": PlayerMapper.PROP_TEAM_CODE,
            "rich_text": {"equals": team_code},
        }
        return self.find_by_filter(filter)

    def find_starters(self, team_code: str) -> list[Player]:
        filter = {
            "and": [
                {
                    "property": PlayerMapper.PROP_TEAM_CODE,
                    "rich_text": {"equals": team_code},
                },
                {
                    "property": PlayerMapper.PROP_IS_STARTER,
                    "checkbox": {"equals": True},
                }
            ]
        }
        return self.find_by_filter(filter)

    def upsert(self, player: Player) -> dict:
        filter = {
            "property": PlayerMapper.PROP_PLAYER_CODE,
            "title": {"equals": player.player_code},
        }
        pages = self._client.query_database(self.database_id, filter=filter)

        if pages:
            return self.update(pages[0]["id"], player)
        return self.create(player)
    