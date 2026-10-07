import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bulk Certificate Generator API"
    database_url: str = "postgresql+psycopg://certificate:certificate@localhost:5432/certificates"
    generated_certificates_dir: Path = Path("generated_certificates")
    max_recipients_per_job: int = Field(default=1000, ge=1, le=10000)
    default_page_size: int = Field(default=20, ge=1, le=100)
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.app_name)


settings = Settings()