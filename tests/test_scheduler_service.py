from unittest.mock import MagicMock, call, patch

from app.services.crawler.parser import ScheduledGame
from app.services.scheduler.scheduler_service import SchedulerService

from datetime import time


class TestScheduleDailyGames:

    def test_resets_today_game_status_before_crawling(self):
        mock_schedule_crawler = MagicMock()
        mock_schedule_crawler.get_today_games.return_value = []
        mock_discord = MagicMock()
        mock_team_repo = MagicMock()
        mock_team_repo.reset_today_game_status.return_value = 0

        service = SchedulerService(
            schedule_crawler=mock_schedule_crawler,
            discord_notifier=mock_discord,
            team_repository=mock_team_repo,
        )
        service._schedule_daily_games()

        mock_team_repo.reset_today_game_status.assert_called_once()

    def test_reset_called_before_get_today_games(self):
        call_order = []

        mock_schedule_crawler = MagicMock()
        mock_schedule_crawler.get_today_games.side_effect = lambda: (
            call_order.append("get_today_games") or []
        )
        mock_discord = MagicMock()
        mock_team_repo = MagicMock()
        mock_team_repo.reset_today_game_status.side_effect = lambda: (
            call_order.append("reset") or 0
        )

        service = SchedulerService(
            schedule_crawler=mock_schedule_crawler,
            discord_notifier=mock_discord,
            team_repository=mock_team_repo,
        )
        service._schedule_daily_games()

        assert call_order == ["reset", "get_today_games"]

    def test_cache_reset_called_when_teams_reset(self):
        mock_schedule_crawler = MagicMock()
        mock_schedule_crawler.get_today_games.return_value = []
        mock_discord = MagicMock()
        mock_team_repo = MagicMock()
        mock_team_repo.reset_today_game_status.return_value = 3
        mock_cache_reset = MagicMock()

        service = SchedulerService(
            schedule_crawler=mock_schedule_crawler,
            discord_notifier=mock_discord,
            team_repository=mock_team_repo,
            cache_reset_service=mock_cache_reset,
        )
        service._schedule_daily_games()

        mock_cache_reset.reset.assert_called_once()

    def test_marks_today_game_teams_when_games_exist(self):
        games = [
            ScheduledGame(game_id="id1", start_time=time(14, 0), home_team_code="lg", away_team_code="kt"),
            ScheduledGame(game_id="id2", start_time=time(14, 0), home_team_code="nc", away_team_code="ob"),
        ]
        mock_schedule_crawler = MagicMock()
        mock_schedule_crawler.get_today_games.return_value = games
        mock_discord = MagicMock()
        mock_team_repo = MagicMock()
        mock_team_repo.reset_today_game_status.return_value = 0
        mock_cache_reset = MagicMock()

        service = SchedulerService(
            schedule_crawler=mock_schedule_crawler,
            discord_notifier=mock_discord,
            team_repository=mock_team_repo,
            cache_reset_service=mock_cache_reset,
        )
        service._schedule_daily_games()

        set_calls = mock_team_repo.set_today_game_status.call_args_list
        called_teams = {c[0][0] for c in set_calls}
        assert called_teams == {"lg", "kt", "nc", "ob"}
        for c in set_calls:
            assert c[0][1] is True
        mock_cache_reset.reset.assert_called()

    def test_does_not_mark_teams_when_no_games(self):
        mock_schedule_crawler = MagicMock()
        mock_schedule_crawler.get_today_games.return_value = []
        mock_discord = MagicMock()
        mock_team_repo = MagicMock()
        mock_team_repo.reset_today_game_status.return_value = 0

        service = SchedulerService(
            schedule_crawler=mock_schedule_crawler,
            discord_notifier=mock_discord,
            team_repository=mock_team_repo,
        )
        service._schedule_daily_games()

        mock_team_repo.set_today_game_status.assert_not_called()

    def test_cache_reset_not_called_when_no_teams_reset(self):
        mock_schedule_crawler = MagicMock()
        mock_schedule_crawler.get_today_games.return_value = []
        mock_discord = MagicMock()
        mock_team_repo = MagicMock()
        mock_team_repo.reset_today_game_status.return_value = 0
        mock_cache_reset = MagicMock()

        service = SchedulerService(
            schedule_crawler=mock_schedule_crawler,
            discord_notifier=mock_discord,
            team_repository=mock_team_repo,
            cache_reset_service=mock_cache_reset,
        )
        service._schedule_daily_games()

        mock_cache_reset.reset.assert_not_called()

    def test_cron_trigger_is_0_05(self):
        mock_schedule_crawler = MagicMock()
        mock_discord = MagicMock()
        mock_team_repo = MagicMock()

        service = SchedulerService(
            schedule_crawler=mock_schedule_crawler,
            discord_notifier=mock_discord,
            team_repository=mock_team_repo,
        )

        with patch.object(service._scheduler, "add_job") as mock_add_job, \
             patch.object(service._scheduler, "start"):
            service._schedule_daily_games = MagicMock()
            service.start()

            trigger = mock_add_job.call_args.kwargs["trigger"]
            fields = {f.name: str(f) for f in trigger.fields}
            assert fields["hour"] == "0"
            assert fields["minute"] == "5"
