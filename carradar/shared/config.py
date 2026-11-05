from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    bot_token: str
    admin_ids: str = ""
    webapp_url: str = ""
    database_url: str
    poll_interval_sec: int = 60

    @field_validator("database_url")
    @classmethod
    def _asyncpg(cls, v: str) -> str:
        # Neon gives a libpq URL; asyncpg wants ssl=require and rejects sslmode/channel_binding.
        v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v.split("?")[0] + "?ssl=require" if "neon.tech" in v else v

    @property
    def admins(self) -> set[int]:
        return {int(x) for x in self.admin_ids.split(",") if x.strip()}


settings = Settings()
