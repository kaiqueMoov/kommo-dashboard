from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "kommo-dashboard"
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    DATABASE_URL: str
    KOMMO_BASE_URL: str
    KOMMO_LONG_LIVED_TOKEN: str

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()