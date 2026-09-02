from app.config import settings
from app.models import Player
from app.repositories.base import BaseRepository, UpsertResult
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

    def reset_starters(self, team_code: str, keep_codes: set[str] | None = None) -> int:
        filter = {
            "and": [
                {
                    "property": PlayerMapper.PROP_TEAM_CODE,
                    "rich_text": {"equals": team_code},
                },
                {
                    "property": PlayerMapper.PROP_IS_STARTER,
                    "checkbox": {"equals": True},
                },
            ]
        }
        pages = self._client.query_database(self.database_id, filter=filter)

        reset_properties = {
            PlayerMapper.PROP_IS_STARTER: {"checkbox": False},
            PlayerMapper.PROP_BATTING_ORDER: {"number": None},
        }

        keep_codes = keep_codes or set()
        reset_count = 0

        for page in pages:
            if self._mapper.to_model(page).player_code in keep_codes:
                continue
            self._client.update_page(page["id"], reset_properties)
            reset_count += 1

        return reset_count

    def upsert(self, player: Player) -> UpsertResult:
        filter = {
            "property": PlayerMapper.PROP_PLAYER_CODE,
            "title": {"equals": player.player_code},
        }
        pages = self._client.query_database(self.database_id, filter=filter)

        if pages:
            response = self.update(pages[0]["id"], player)
            return UpsertResult(created=False, response=response)
        response = self.create(player)
        return UpsertResult(created=True, response=response)
    