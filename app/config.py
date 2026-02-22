from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://aggregator:aggregator@localhost:5432/aggregator"
    offers_service_url: str
    offers_refresh_token: SecretStr
    sync_schedule: str | None = "*/30 * * * * *"  # sec min hour day month dow
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}

    @model_validator(mode="after")
    def normalize_database_url(self) -> "Settings":
        """Render provides postgres:// or postgresql:// — rewrite for asyncpg."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        self.database_url = url
        return self


settings = Settings()
