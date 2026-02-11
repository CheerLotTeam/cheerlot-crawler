from dataclasses import dataclass, field
from pydantic import BaseModel


@dataclass
class NewPlayerInfo:
    player_code: str
    name: str
    team_code: str
    back_number: int
    position: str


@dataclass
class CrawlResult:
    game_id: str
    success: bool
    home_team_code: str | None = None
    away_team_code: str | None = None
    players_saved: int = 0
    error_message: str | None = None
    new_players: list[NewPlayerInfo] = field(default_factory=list)

class GameCrawlResponse(BaseModel):
    game_id: str
    success: bool
    home_team_code: str | None = None
    away_team_code: str | None = None
    players_saved: int = 0
    error_message: str | None = None

    @classmethod
    def from_result(cls, result: CrawlResult) -> "GameCrawlResponse":
        return cls(
            game_id=result.game_id,
            success=result.success,
            home_team_code=result.home_team_code,
            away_team_code=result.away_team_code,
            players_saved=result.players_saved,
            error_message=result.error_message,
        )

class TodayCrawlResponse(BaseModel):
    total_games: int
    success_count: int
    fail_count: int
    results: list[GameCrawlResponse]
