from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    database_url: str = "postgresql+asyncpg://localhost/flightplan_dev"
    default_tenant_id: str = "00000000-0000-0000-0000-000000000000"
    plugins_dir: str = "plugins"


@lru_cache
def get_settings() -> Settings:
    return Settings()
