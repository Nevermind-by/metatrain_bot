from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_path: str = "data/metatrain.db"
    web_app_url: str | None = None
    render_external_url: str | None = None
    webhook_secret: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
