import os
import sys

APP_NAME = os.getenv("APP_NAME", "sports-scores-job")
APP_VERSION = "0.0.1"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT: str = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME: str = os.getenv("DATABASE_NAME", "sportscores")
PGUSER: str = os.getenv("PGUSER", "sportadmin")
PGPASSWORD: str = os.getenv("PGPASSWORD", "postgres")
DATABASE_URL: str = f"postgresql://{PGUSER}:{PGPASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "https://trmnl.com/api/custom_plugins/")

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(process)d] [%(levelname)s] in %(module)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "default",
        },
         "stderr": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "default",
        }
    },
    "loggers": {
        "__main__": {
            "level": LOG_LEVEL,
            "handlers": ["stdout"],
            "propagate": False,
        }
    },
    "root": {"level": LOG_LEVEL, "handlers": ["stdout"]},
}