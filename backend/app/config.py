from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads settings from environment variables (names are case-insensitive)."""

    model_config = SettingsConfigDict(extra="ignore")

    database_url: str  # required: the app refuses to start if DATABASE_URL is missing
    environment: str = "development" 

settings = Settings()