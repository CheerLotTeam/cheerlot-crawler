from app.models import Player
from app.infrastructure.notion.mappers.base import BaseMapper

class PlayerMapper(BaseMapper[Player]):

    PROP_PLAYER_CODE = "선수코드"
    PROP_TEAM_CODE = "팀코드"
    PROP_NAME = "이름"
    PROP_BACK_NUMBER = "등번호"
    PROP_POSITION = "포지션"
    PROP_BAT_THROW = "타격투구"
    PROP_BATTING_ORDER = "타순"
    PROP_IS_STARTER = "선발여부"

    def to_properties(self, model: Player) -> dict:
        properties = {
            self.PROP_PLAYER_CODE: self._make_title(model.player_code),
            self.PROP_TEAM_CODE: self._make_rich_text(model.team_code),
            self.PROP_NAME: self._make_rich_text(model.name),
            self.PROP_BACK_NUMBER: self._make_number(model.back_number),
            self.PROP_POSITION: self._make_rich_text(model.position),
            self.PROP_BAT_THROW: self._make_rich_text(model.bat_throw),
            self.PROP_IS_STARTER: self._make_checkbox(model.is_starter),
        }

        if model.batting_order is not None:
            properties[self.PROP_BATTING_ORDER] = self._make_number(model.batting_order)
        return properties

    def to_model(self, page: dict) -> Player:
        props = page["properties"]

        return Player(
            player_code=self._get_title(props, self.PROP_PLAYER_CODE),
            team_code=self._get_rich_text(props, self.PROP_TEAM_CODE),
            name=self._get_rich_text(props, self.PROP_NAME),
            back_number=self._get_number(props, self.PROP_BACK_NUMBER) or 0,
            position=self._get_rich_text(props, self.PROP_POSITION),
            bat_throw=self._get_rich_text(props, self.PROP_BAT_THROW),
            batting_order=self._get_number(props, self.PROP_BATTING_ORDER),
            is_starter=self._get_checkbox(props, self.PROP_IS_STARTER),
        )
