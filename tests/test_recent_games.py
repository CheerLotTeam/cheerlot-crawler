from unittest.mock import patch, MagicMock
from datetime import date

from app.services.crawler.parser import PreviewParser, ScheduleParser
from app.services.crawler.recent_games import RecentGamesService


def _make_schedule_response(date_entries: list[dict]) -> dict:
    return {
        "code": 200,
        "success": True,
        "result": {
            "today": "20260327",
            "dates": date_entries,
        },
    }


def _make_preview_response(
    h_code: str,
    a_code: str,
    home_starter: str | None = None,
    away_starter: str | None = None,
) -> dict:
    result = {
        "code": 200,
        "success": True,
        "result": {
            "previewData": {
                "gameInfo": {
                    "hCode": h_code,
                    "aCode": a_code,
                },
                "homeStarter": {},
                "awayStarter": {},
            },
        },
    }

    if home_starter:
        result["result"]["previewData"]["homeStarter"] = {
            "playerInfo": {"name": home_starter}
        }
    if away_starter:
        result["result"]["previewData"]["awayStarter"] = {
            "playerInfo": {"name": away_starter}
        }

    return result


class TestPreviewParserGameSummary:

    def test_parse_game_summary(self):
        parser = PreviewParser()
        data = _make_preview_response("LG", "KT", "이민호", "쿠에바스")

        result = parser.parse_game_summary(data)

        assert result is not None
        assert result.home_team_code == "lg"
        assert result.away_team_code == "kt"
        assert result.home_starter_name == "이민호"
        assert result.away_starter_name == "쿠에바스"

    def test_parse_game_summary_no_starters(self):
        parser = PreviewParser()
        data = _make_preview_response("OB", "SS")

        result = parser.parse_game_summary(data)

        assert result is not None
        assert result.home_team_code == "ob"
        assert result.away_team_code == "ss"
        assert result.home_starter_name is None
        assert result.away_starter_name is None

    def test_parse_game_summary_invalid_response(self):
        parser = PreviewParser()
        data = {"code": 500, "success": False}

        result = parser.parse_game_summary(data)

        assert result is None

    def test_parse_game_summary_no_preview_data(self):
        parser = PreviewParser()
        data = {"code": 200, "success": True, "result": {"previewData": None}}

        result = parser.parse_game_summary(data)

        assert result is None

    def test_parse_game_summary_no_game_info(self):
        parser = PreviewParser()
        data = {"code": 200, "success": True, "result": {"previewData": {}}}

        result = parser.parse_game_summary(data)

        assert result is None


class TestScheduleParserByDate:

    def test_parse_game_ids_by_date(self):
        parser = ScheduleParser()
        data = _make_schedule_response([
            {"ymd": "20260327", "gameIds": ["20260327LGKT00000"]},
            {"ymd": "20260326", "gameIds": []},
            {"ymd": "20260325", "gameIds": ["20260325HTLG00000"]},
        ])

        result = parser.parse_game_ids_by_date(data, "20260325")

        assert result == ["20260325HTLG00000"]

    def test_parse_game_ids_by_date_not_found(self):
        parser = ScheduleParser()
        data = _make_schedule_response([
            {"ymd": "20260327", "gameIds": ["20260327LGKT00000"]},
        ])

        result = parser.parse_game_ids_by_date(data, "20260320")

        assert result == []

    def test_parse_game_ids_filters_invalid_length(self):
        parser = ScheduleParser()
        data = _make_schedule_response([
            {"ymd": "20260327", "gameIds": ["20260327LGKT00000", "SHORT"]},
        ])

        result = parser.parse_game_ids_by_date(data, "20260327")

        assert result == ["20260327LGKT00000"]


class TestRecentGamesService:

    def _create_service(self, mock_client, today: date = date(2026, 3, 27)):
        service = RecentGamesService(client=mock_client)
        service._get_today = lambda: today
        return service

    def test_get_recent_games_success(self):
        mock_client = MagicMock()
        schedule_data = _make_schedule_response([
            {"ymd": "20260327", "gameIds": ["20260327LGKT00000", "20260327OBSS00000"]},
            {"ymd": "20260326", "gameIds": []},
            {"ymd": "20260325", "gameIds": ["20260325HTLG00000"]},
        ])
        mock_client.get_schedule.return_value = schedule_data
        mock_client.get_game_preview.side_effect = [
            _make_preview_response("LG", "KT", "이민호", "쿠에바스"),
            _make_preview_response("OB", "SS"),
            _make_preview_response("HT", "LG", "양현종", "이민호"),
        ]

        service = self._create_service(mock_client)
        result = service.get_recent_games()

        assert len(result.schedules) == 3

        today = result.schedules[0]
        assert today.date == "2026-03-27"
        assert len(today.games) == 2
        assert today.games[0].homeTeamCode == "lg"
        assert today.games[0].awayTeamCode == "kt"
        assert today.games[0].homeStarterPitcherName == "이민호"
        assert today.games[0].awayStarterPitcherName == "쿠에바스"
        assert today.games[1].homeTeamCode == "ob"
        assert today.games[1].awayTeamCode == "ss"
        assert today.games[1].homeStarterPitcherName is None

        yesterday = result.schedules[1]
        assert yesterday.date == "2026-03-26"
        assert yesterday.games == []

        day_before = result.schedules[2]
        assert day_before.date == "2026-03-25"
        assert len(day_before.games) == 1
        assert day_before.games[0].homeTeamCode == "ht"
        assert day_before.games[0].awayTeamCode == "lg"
        assert day_before.games[0].homeStarterPitcherName == "양현종"
        assert day_before.games[0].awayStarterPitcherName == "이민호"

    def test_get_recent_games_schedule_failure(self):
        mock_client = MagicMock()
        mock_client.get_schedule.return_value = None

        service = self._create_service(mock_client)
        result = service.get_recent_games()

        assert len(result.schedules) == 3
        for schedule in result.schedules:
            assert schedule.games == []

    def test_get_recent_games_preview_failure(self):
        mock_client = MagicMock()
        schedule_data = _make_schedule_response([
            {"ymd": "20260327", "gameIds": ["20260327LGKT00000"]},
            {"ymd": "20260326", "gameIds": []},
            {"ymd": "20260325", "gameIds": []},
        ])
        mock_client.get_schedule.return_value = schedule_data
        mock_client.get_game_preview.return_value = None

        service = self._create_service(mock_client)
        result = service.get_recent_games()

        assert len(result.schedules) == 3
        assert result.schedules[0].games == []

    def test_cross_month_dates_fetch_separate_schedules(self):
        mock_client = MagicMock()
        april_data = _make_schedule_response([
            {"ymd": "20260401", "gameIds": ["20260401LGKT00000"]},
        ])
        march_data = _make_schedule_response([
            {"ymd": "20260331", "gameIds": []},
            {"ymd": "20260330", "gameIds": []},
        ])
        mock_client.get_schedule.side_effect = [april_data, march_data]
        mock_client.get_game_preview.return_value = _make_preview_response("LG", "KT")

        service = self._create_service(mock_client, today=date(2026, 4, 1))
        result = service.get_recent_games()

        assert mock_client.get_schedule.call_count == 2
        assert len(result.schedules) == 3

    def test_same_month_reuses_schedule_cache(self):
        mock_client = MagicMock()
        schedule_data = _make_schedule_response([
            {"ymd": "20260327", "gameIds": []},
            {"ymd": "20260326", "gameIds": []},
            {"ymd": "20260325", "gameIds": []},
        ])
        mock_client.get_schedule.return_value = schedule_data

        service = self._create_service(mock_client)
        service.get_recent_games()

        assert mock_client.get_schedule.call_count == 1


class TestRecentGamesEndpoint:

    @patch("app.routers.games.RecentGamesService")
    def test_get_recent_games_endpoint(self, mock_service_cls, client):
        from app.schemas.game import RecentGamesResponse, DaySchedule, GameSchedule

        mock_service = MagicMock()
        mock_service.get_recent_games.return_value = RecentGamesResponse(
            schedules=[
                DaySchedule(date="2026-03-27", games=[
                    GameSchedule(
                        homeTeamCode="lg",
                        awayTeamCode="kt",
                        homeStarterPitcherName="이민호",
                        awayStarterPitcherName="쿠에바스",
                    ),
                ]),
                DaySchedule(date="2026-03-26", games=[]),
                DaySchedule(date="2026-03-25", games=[]),
            ]
        )
        mock_service_cls.return_value = mock_service

        response = client.get("/api/games/recent")

        assert response.status_code == 200
        data = response.json()
        assert len(data["schedules"]) == 3
        assert data["schedules"][0]["date"] == "2026-03-27"
        assert len(data["schedules"][0]["games"]) == 1
        assert data["schedules"][0]["games"][0]["homeTeamCode"] == "lg"
        assert data["schedules"][0]["games"][0]["homeStarterPitcherName"] == "이민호"

    @patch("app.routers.games.RecentGamesService")
    def test_get_recent_games_endpoint_error(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service.get_recent_games.side_effect = Exception("크롤링 실패")
        mock_service_cls.return_value = mock_service

        response = client.get("/api/games/recent")

        assert response.status_code == 500
        assert response.json() == {"error": "크롤링 실패"}
