import logging

from app.config import settings
from app.models import Team
from app.repositories.base import BaseRepository, UpsertResult
from app.infrastructure.notion.mappers import BaseMapper, TeamMapper

logger = logging.getLogger(__name__)


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

    def reset_today_game_status(self) -> int:
        teams = self.find_teams_with_today_game()
        if not teams:
            logger.info("리셋할 팀 없음 (has_today_game=True인 팀 없음)")
            return 0

        for team in teams:
            filter = {
                "property": TeamMapper.PROP_TEAM_CODE,
                "title": {"equals": team.team_code},
            }
            pages = self._client.query_database(self.database_id, filter=filter)
            if pages:
                self._client.update_page(
                    pages[0]["id"],
                    {TeamMapper.PROP_HAS_TODAY_GAME: {"checkbox": False}},
                )

        logger.info(f"{len(teams)}개 팀 has_today_game 리셋 완료")
        return len(teams)

    def upsert(self, team: Team) -> UpsertResult:
        filter = {
            "property": TeamMapper.PROP_TEAM_CODE,
            "title": {"equals": team.team_code},
        }
        pages = self._client.query_database(self.database_id, filter=filter)

        if pages:
            response = self.update(pages[0]["id"], team)
            return UpsertResult(created=False, response=response)
        response = self.create(team)
        return UpsertResult(created=True, response=response)