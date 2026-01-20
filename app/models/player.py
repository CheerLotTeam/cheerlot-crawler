from pydantic import BaseModel, Field

class PlayerBase(BaseModel):
    player_code: str = Field(..., max_length=20)
    team_code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=50)
    back_number: int = Field(..., ge=0, le=99)
    position: str = Field(..., max_length=20)
    bat_throw: str = Field(..., max_length=10)

class PlayerGameStatus(BaseModel):
    batting_order: int | None = Field(None, ge=1, le=9)
    is_starter: bool = False

class Player(PlayerBase):
    batting_order: int | None = Field(None, ge=1, le=9)
    is_starter: bool = False

class PlayerCreate(PlayerBase):
    pass
