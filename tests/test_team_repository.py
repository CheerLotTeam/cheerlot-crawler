from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models import Team
from app.repositories.team_repository import TeamRepository
from app.infrastructure.notion.mappers import TeamMapper


class TestResetTodayGameStatus:

    def _create_repository(self, mock_client):
        repo = TeamRepository.__new__(TeamRepository)
        repo._client = mock_client
        repo._mapper = TeamMapper()
        return repo

    def test_resets_teams_with_today_game(self):
        mock_client = MagicMock()

        team = Team(
            team_code="hh",
            team_name="한화",
            has_today_game=True,
            updated_at=datetime.now(),
        )

        mock_client.query_database.side_effect = [
            [{"id": "page-1", "properties": self._make_team_props(team)}],
            [{"id": "page-1"}],
        ]

        repo = self._create_repository(mock_client)
        count = repo.reset_today_game_status()

        assert count == 1
        mock_client.update_page.assert_called_once_with(
            "page-1",
            {
                "has_today_game": {"checkbox": False},
                "is_lineup_updated_today": {"checkbox": False},
            },
        )

    def test_resets_multiple_teams(self):
        mock_client = MagicMock()

        teams = [
            Team(team_code="hh", team_name="한화", has_today_game=True, updated_at=datetime.now()),
            Team(team_code="lg", team_name="LG", has_today_game=True, updated_at=datetime.now()),
        ]

        mock_client.query_database.side_effect = [
            [{"id": f"page-{i}", "properties": self._make_team_props(t)} for i, t in enumerate(teams)],
            [{"id": "page-0"}],
            [{"id": "page-1"}],
        ]

        repo = self._create_repository(mock_client)
        count = repo.reset_today_game_status()

        assert count == 2
        assert mock_client.update_page.call_count == 2

    def test_no_teams_returns_zero(self):
        mock_client = MagicMock()
        mock_client.query_database.return_value = []

        repo = self._create_repository(mock_client)
        count = repo.reset_today_game_status()

        assert count == 0
        mock_client.update_page.assert_not_called()

    def _make_team_props(self, team: Team) -> dict:
        return {
            "team_code": {"title": [{"plain_text": team.team_code}]},
            "team_name": {"rich_text": [{"plain_text": team.team_name}]},
            "has_today_game": {"checkbox": team.has_today_game},
            "is_season_ended": {"checkbox": False},
            "updated_at": {"date": {"start": team.updated_at.strftime("%Y-%m-%d")}},
            "opponent_team_code": {"rich_text": []},
            "starter_pitcher_name": {"rich_text": []},
            "last_game_date": {"date": None},
        }
