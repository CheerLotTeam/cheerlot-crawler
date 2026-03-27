from unittest.mock import MagicMock, patch

from app.services.scheduler.scheduler_service import SchedulerService


class TestScheduleDailyGames:

    def test_resets_today_game_status_before_crawling(self):
        mock_schedule_crawler = MagicMock()
        mock_schedule_crawler.get_today_games.return_value = []
        mock_discord = MagicMock()
        mock_team_repo = MagicMock()

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
