"""Application configuration, loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed access to config values - avoids scattering `os.getenv()` calls everywhere."""

    database_url: str
    jwt_secret_key: str

    # Tells pydantic-settings to read values from a `.env` file in the backend/ folder.
    model_config = SettingsConfigDict(env_file=".env")


# Single shared instance - imported wherever config is needed (e.g. `from app.core.config import settings`).
settings = Settings()
