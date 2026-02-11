from datetime import time
from unittest.mock import patch, MagicMock

import httpx
import pytest

from app.schemas.crawl import CrawlResult, NewPlayerInfo
from app.services.crawler.parser import ScheduledGame
from app.services.discord_notifier import DiscordNotifier


@pytest.fixture
def notifier():
    return DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")


@pytest.fixture
def disabled_notifier():
    return DiscordNotifier(webhook_url="")


class TestIsEnabled:
    def test_enabled_with_url(self, notifier):
        assert notifier._is_enabled() is True

    def test_disabled_without_url(self, disabled_notifier):
        assert disabled_notifier._is_enabled() is False


class TestSendDailySchedule:
    @patch("app.services.discord_notifier.httpx.Client")
    def test_sends_games(self, mock_client_cls, notifier):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = MagicMock(status_code=204)

        games = [
            ScheduledGame(
                game_id="20260211OBHT0",
                start_time=time(18, 30),
                home_team_code="ht",
                away_team_code="ob",
            ),
        ]

        notifier.send_daily_schedule(games)

        mock_client.post.assert_called_once()
        payload = mock_client.post.call_args[1]["json"]
        assert payload["username"] == "Cheerlot Crawler"
        assert len(payload["embeds"]) == 1
        assert "KBO 오늘의 경기" in payload["embeds"][0]["title"]
        assert "두산 베어스" in payload["embeds"][0]["description"]
        assert "KIA 타이거즈" in payload["embeds"][0]["description"]

    @patch("app.services.discord_notifier.httpx.Client")
    def test_sends_no_games(self, mock_client_cls, notifier):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = MagicMock(status_code=204)

        notifier.send_daily_schedule([])

        payload = mock_client.post.call_args[1]["json"]
        assert "경기 없음" in payload["embeds"][0]["description"]

    def test_skips_when_disabled(self, disabled_notifier):
        with patch("app.services.discord_notifier.httpx.Client") as mock:
            disabled_notifier.send_daily_schedule([])
            mock.assert_not_called()


class TestSendLineupResult:
    @patch("app.services.discord_notifier.httpx.Client")
    def test_sends_success(self, mock_client_cls, notifier):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = MagicMock(status_code=204)

        result = CrawlResult(
            game_id="20260211OBHT0",
            success=True,
            home_team_code="ht",
            away_team_code="ob",
            players_saved=18,
            new_players=[
                NewPlayerInfo("ht99", "김민수", "ht", 99, "투수"),
            ],
        )

        notifier.send_lineup_result(result)

        payload = mock_client.post.call_args[1]["json"]
        embed = payload["embeds"][0]
        assert "크롤링 완료" in embed["title"]
        assert embed["color"] == 0x2ECC71
        assert "18명" in embed["description"]
        assert "신규 선수: 1명" in embed["description"]

    @patch("app.services.discord_notifier.httpx.Client")
    def test_sends_failure(self, mock_client_cls, notifier):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = MagicMock(status_code=204)

        result = CrawlResult(
            game_id="20260211OBHT0",
            success=False,
            error_message="라인업 조회 실패",
        )

        notifier.send_lineup_result(result)

        payload = mock_client.post.call_args[1]["json"]
        embed = payload["embeds"][0]
        assert "크롤링 실패" in embed["title"]
        assert embed["color"] == 0xE74C3C


class TestSendNewPlayers:
    @patch("app.services.discord_notifier.httpx.Client")
    def test_sends_new_players(self, mock_client_cls, notifier):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = MagicMock(status_code=204)

        new_players = [
            NewPlayerInfo("ht99", "김민수", "ht", 99, "투수"),
            NewPlayerInfo("ob07", "이준호", "ob", 7, "외야수"),
        ]

        notifier.send_new_players(new_players)

        payload = mock_client.post.call_args[1]["json"]
        embed = payload["embeds"][0]
        assert "신규 선수 등록" in embed["title"]
        assert embed["color"] == 0xF39C12
        assert "김민수" in embed["description"]
        assert "이준호" in embed["description"]
        assert "2명" in embed["footer"]["text"]

    def test_skips_empty_list(self, notifier):
        with patch("app.services.discord_notifier.httpx.Client") as mock:
            notifier.send_new_players([])
            mock.assert_not_called()


class TestErrorHandling:
    @patch("app.services.discord_notifier.httpx.Client")
    def test_http_error_does_not_raise(self, mock_client_cls, notifier):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response,
        )
        mock_client.post.return_value = mock_response

        notifier.send_daily_schedule([])

    @patch("app.services.discord_notifier.httpx.Client")
    def test_request_error_does_not_raise(self, mock_client_cls, notifier):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.RequestError("Connection failed")

        notifier.send_daily_schedule([])
