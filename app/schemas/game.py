from pydantic import BaseModel


class GameSchedule(BaseModel):
    homeTeamCode: str
    awayTeamCode: str
    homeStarterPitcherName: str | None = None
    awayStarterPitcherName: str | None = None


class DaySchedule(BaseModel):
    date: str
    games: list[GameSchedule]


class RecentGamesResponse(BaseModel):
    schedules: list[DaySchedule]
