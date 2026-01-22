from dataclasses import dataclass
from datetime import date
from typing import Any

KBO_GAME_ID_LENGTH = 17

@dataclass
class LineupPlayer:
    name: str
    bat_order: int
    position: str
    back_number: str | None = None
    bats_throws: str | None = None

@dataclass
class GameLineup:
    home_team_code: str
    away_team_code: str
    home_players: list[LineupPlayer]
    away_players: list[LineupPlayer]
    game_date: date | None = None
    home_starter_name: str | None = None
    away_starter_name: str | None = None

class PreviewParser:

    def parse(self, data: dict[str, Any]) -> GameLineup | None:
        if not self._is_valid_response(data):
            return None

        preview_data = data["result"]["previewData"]
        game_info = preview_data["gameInfo"]

        home_lineup = preview_data.get("homeTeamLineUp", {}).get("fullLineUp", [])
        away_lineup = preview_data.get("awayTeamLineUp", {}).get("fullLineUp", [])

        if not self._has_lineup(home_lineup) or not self._has_lineup(away_lineup):
            return None

        home_starter = preview_data.get("homeStarter", {})
        away_starter = preview_data.get("awayStarter", {})
        game_date = self._parse_game_date(game_info.get("gdate"))

        return GameLineup(
            home_team_code=game_info["hCode"],
            away_team_code=game_info["aCode"],
            home_players=self._parse_players(home_lineup),
            away_players=self._parse_players(away_lineup),
            game_date=game_date,
            home_starter_name=home_starter.get("playerInfo", {}).get("name"),
            away_starter_name=away_starter.get("playerInfo", {}).get("name"),
        )

    def _is_valid_response(self, data: dict) -> bool:
        return data.get("code") == 200 and data.get("success") is True

    def _parse_game_date(self, gdate: str | int | None) -> date | None:
        if not gdate:
            return None
        try:
            gdate_str = str(gdate)
            return date(int(gdate_str[:4]), int(gdate_str[4:6]), int(gdate_str[6:8]))
        except (ValueError, IndexError):
            return None

    def _has_lineup(self, lineup: list[dict]) -> bool:
        return any("batorder" in player for player in lineup)

    def _parse_players(self, lineup: list[dict]) -> list[LineupPlayer]:
        players = []

        for player_data in lineup:
            if "batorder" not in player_data:
                continue

            player = LineupPlayer(
                name=player_data["playerName"],
                bat_order=int(player_data["batorder"]),
                position=player_data.get("positionName", ""),
                back_number=player_data.get("backnum", ""),
                bats_throws=player_data.get("batsThrows"),
            )
            players.append(player)

        return players

class ScheduleParser:

    def parse_today_game_ids(self, data: dict[str, Any]) -> list[str]:
        if not self._is_valid_response(data):
            return []

        result = data["result"]
        today = result["today"]

        for date_node in result.get("dates", []):
            if date_node.get("ymd") == today:
                game_ids = date_node.get("gameIds", [])
                return [gid for gid in game_ids if len(gid) == KBO_GAME_ID_LENGTH]

        return []

    def _is_valid_response(self, data: dict[str, Any]) -> bool:
        return data.get("code") == 200 and data.get("success") is True
