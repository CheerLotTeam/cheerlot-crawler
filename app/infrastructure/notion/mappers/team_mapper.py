from datetime import date, datetime

from app.models import Team
from app.infrastructure.notion.mappers.base import BaseMapper

class TeamMapper(BaseMapper[Team]):

    PROP_TEAM_CODE = "team_code"
    PROP_TEAM_NAME = "team_name"
    PROP_HAS_TODAY_GAME = "has_today_game"
    PROP_OPPONENT_CODE = "opponent_team_code"
    PROP_STARTER_PITCHER = "starter_pitcher_name"
    PROP_LAST_GAME_DATE = "last_game_date"
    PROP_SEASON_ENDED = "is_season_ended"
    PROP_UPDATED_AT = "updated_at"

    def to_properties(self, model: Team) -> dict:
        properties = {
            self.PROP_TEAM_CODE: self._make_title(model.team_code),
            self.PROP_TEAM_NAME: self._make_rich_text(model.team_name),
            self.PROP_HAS_TODAY_GAME: self._make_checkbox(model.has_today_game),
            self.PROP_SEASON_ENDED: self._make_checkbox(model.is_season_ended),
            self.PROP_UPDATED_AT: self._make_date(model.updated_at.strftime("%Y-%m-%d") if model.updated_at else None),
        }

        if model.opponent_team_code:
            properties[self.PROP_OPPONENT_CODE] = self._make_rich_text(model.opponent_team_code)

        if model.starter_pitcher_name:
            properties[self.PROP_STARTER_PITCHER] = self._make_rich_text(model.starter_pitcher_name)

        if model.last_game_date:
            properties[self.PROP_LAST_GAME_DATE] = self._make_date(
                model.last_game_date.strftime("%Y-%m-%d")
            )

        return properties

    def to_model(self, page: dict) -> Team:
        props = page["properties"]

        last_game_str = self._get_date(props, self.PROP_LAST_GAME_DATE)
        updated_at_str = self._get_date(props, self.PROP_UPDATED_AT)

        return Team(
            team_code=self._get_title(props, self.PROP_TEAM_CODE),
            team_name=self._get_rich_text(props, self.PROP_TEAM_NAME),
            has_today_game=self._get_checkbox(props, self.PROP_HAS_TODAY_GAME),
            opponent_team_code=self._get_rich_text(props, self.PROP_OPPONENT_CODE) or None,
            starter_pitcher_name=self._get_rich_text(props, self.PROP_STARTER_PITCHER) or None,
            last_game_date=date.fromisoformat(last_game_str) if last_game_str else None,
            is_season_ended=self._get_checkbox(props, self.PROP_SEASON_ENDED),
            updated_at=datetime.fromisoformat(updated_at_str) if updated_at_str else datetime.now(),
        )