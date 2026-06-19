import os
import uuid
import sys
import logging
import hashlib
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Any, Dict
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "monitor-agent"
    APP_VERSION: str = "0.0.1"
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", uuid.uuid4().hex)
    APP_URL: str = os.getenv("APP_URL", "http://127.0.0.1:5001")
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG").upper()
    LOG_JSON: bool = os.getenv("LOG_JSON", "false").lower() == "true"

    DEFAULT_POD_LOG_LINES: int = int(os.getenv("DEFAULT_POD_LOG_LINES", 50))

    KUBE_CONFIG_PATH: str = os.getenv("KUBE_CONFIG_PATH", str(Path.home() / ".kube" / "config"))

    # Populated at runtime
    LOG_CONFIG: Dict[str, Any] = {}

    def model_post_init(self, __context: Any) -> None:
        self.LOG_CONFIG = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": (
                        '{"ts":"%(asctime)s","lvl":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
                        if self.LOG_JSON else
                        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
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
