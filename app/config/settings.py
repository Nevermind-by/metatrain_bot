from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_path: str = "data/metatrain.db"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
