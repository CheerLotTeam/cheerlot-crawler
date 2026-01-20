from pydantic import BaseModel, Field

class CheerSongBase(BaseModel):
    player_code: str = Field(..., max_length=20)
    title: str = Field(..., max_length=100)
    lyrics: str
    audio_url: str = Field(..., max_length=255)

class CheerSong(CheerSongBase):
    id: int

class CheerSongCreate(CheerSongBase):
    pass
