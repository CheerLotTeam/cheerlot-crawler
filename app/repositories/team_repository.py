from app.config import settings
from app.models import Team
from app.repositories.base import BaseRepository
from app.infrastructure.notion.mappers import BaseMapper, TeamMapper

class TeamRepository(BaseRepository[Team]):

    @property
    def database_id(self) -> str:
        return settings.notion_team_db_id

    def _create_mapper(self) -> BaseMapper[Team]:
        return TeamMapper()

    def find_by_team_code(self, team_code: str) -> Team | None:
        filter = {
            "property": TeamMapper.PROP_TEAM_CODE,
            "title": {"equals": team_code},
        }
        results = self.find_by_filter(filter)
        return results[0] if results else None

    def find_teams_with_today_game(self) -> list[Team]:
        filter = {
            "property": TeamMapper.PROP_HAS_TODAY_GAME,
            "checkbox": {"equals": True},
        }
        return self.find_by_filter(filter)

    def upsert(self, team: Team) -> dict:
        filter = {
            "property": TeamMapper.PROP_TEAM_CODE,
            "title": {"equals": team.team_code},
        }
        pages = self._client.query_database(self.database_id, filter=filter)

        if pages:
            return self.update(pages[0]["id"], team)
        return self.create(team)