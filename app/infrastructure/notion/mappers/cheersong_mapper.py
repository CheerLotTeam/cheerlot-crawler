from app.models import CheerSong
from app.infrastructure.notion.mappers.base import BaseMapper

class CheerSongMapper(BaseMapper[CheerSong]):

    PROP_PLAYER_CODE = "선수코드"
    PROP_TITLE = "제목"
    PROP_LYRICS = "가사"
    PROP_AUDIO_URL = "음원URL"

    def to_properties(self, model: CheerSong) -> dict:
        return {
            self.PROP_PLAYER_CODE: self._make_title(model.player_code),
            self.PROP_TITLE: self._make_rich_text(model.title),
            self.PROP_LYRICS: self._make_rich_text(model.lyrics),
            self.PROP_AUDIO_URL: self._make_rich_text(model.audio_url),
        }

    def to_model(self, page: dict) -> CheerSong:
        props = page["properties"]

        return CheerSong(
            id=0,
            player_code=self._get_title(props, self.PROP_PLAYER_CODE),
            title=self._get_rich_text(props, self.PROP_TITLE),
            lyrics=self._get_rich_text(props, self.PROP_LYRICS),
            audio_url=self._get_rich_text(props, self.PROP_AUDIO_URL),
        )