from datetime import date, datetime
from pydantic import BaseModel, Field

class TeamBase(BaseModel):
    team_code: str = Field(..., max_length=10)
    team_name: str = Field(..., max_length=100)

class TeamGameStatus(BaseModel):
    has_today_game: bool = False
    opponent_team_code: str | None = None
    starter_pitcher_name: str | None = None
    last_game_date: date | None = None
    is_season_ended: bool = False

class Team(TeamBase):
    has_today_game: bool = False
    opponent_team_code: str | None = Field(None, max_length=10)
    starter_pitcher_name: str | None = Field(None, max_length=50)
    last_game_date: date | None = None
    is_season_ended: bool = False
    updated_at: datetime

class TeamCreate(TeamBase):
    pass
