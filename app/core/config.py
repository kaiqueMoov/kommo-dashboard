from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "kommo-dashboard"
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    DATABASE_URL: str
    KOMMO_BASE_URL: str
    KOMMO_LONG_LIVED_TOKEN: str
    KOMMO_WEBHOOK_SECRET: str | None = None


settings = Settings()