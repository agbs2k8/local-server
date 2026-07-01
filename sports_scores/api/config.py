import logging
import os
import sys
from typing import Any, Dict
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "sports-scores"
    APP_VERSION: str = "0.0.1"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_JSON: bool = False
    LOG_CONFIG: Dict[str, Any] = {}
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: str = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "sportscores")
    PGUSER: str = os.getenv("PGUSER", "sportadmin")
    PGPASSWORD: str = os.getenv("PGPASSWORD", "postgres")
    DATABASE_URL: str = f"postgresql://{PGUSER}:{PGPASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

    def model_post_init(self, __context: Any) -> None:
        self.LOG_CONFIG = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": (
                        '{"ts":"%(asctime)s","lvl":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
                        if self.LOG_JSON
                        else "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
                    ),
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "default",
                }
            },
            "root": {
                "level": self.LOG_LEVEL,
                "handlers": ["console"],
            },
        }

        logging.basicConfig(level=self.LOG_LEVEL)


cfg = Settings()