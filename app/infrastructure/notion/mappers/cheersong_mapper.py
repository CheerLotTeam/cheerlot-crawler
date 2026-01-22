from app.models import CheerSong
from app.infrastructure.notion.mappers.base import BaseMapper

class CheerSongMapper(BaseMapper[CheerSong]):

    PROP_TITLE = "title"
    PROP_PLAYER_CODE = "player_code"
    PROP_LYRICS = "lyrics"
    PROP_AUDIO_FILE_NAME = "audio_file_name"
    PROP_ID = "id"

    def to_properties(self, model: CheerSong) -> dict:
        return {
            self.PROP_TITLE: self._make_title(model.title),
            self.PROP_PLAYER_CODE: self._make_rich_text(model.player_code),
            self.PROP_LYRICS: self._make_rich_text(model.lyrics),
            self.PROP_AUDIO_FILE_NAME: self._make_rich_text(model.audio_url),
        }

    def to_model(self, page: dict) -> CheerSong:
        props = page["properties"]

        return CheerSong(
            player_code=self._get_rich_text(props, self.PROP_PLAYER_CODE),
            title=self._get_title(props, self.PROP_TITLE),
            lyrics=self._get_rich_text(props, self.PROP_LYRICS),
            audio_url=self._get_rich_text(props, self.PROP_AUDIO_FILE_NAME),
        )