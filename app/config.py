from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    notion_api_key: str = ""
    notion_player_db_id: str = ""
    notion_team_db_id: str = ""
    notion_cheersong_db_id: str = ""
    discord_webhook_url: str = ""
    cache_reset_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
