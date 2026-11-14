from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads settings from environment variables (names are case-insensitive)."""

    model_config = SettingsConfigDict(extra="ignore")

    database_url: str  # required: the app refuses to start if DATABASE_URL is missing

    jwt_secret: str = Field(min_length=32)  # signs login tokens; a short key is easy to guess
    
settings = Settings()