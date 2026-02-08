from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://aggregator:aggregator@localhost:5432/aggregator"
    offers_service_url: str
    offers_refresh_token: SecretStr
    sync_schedule: str = "*/30 * * * * *"  # sec min hour day month dow
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
