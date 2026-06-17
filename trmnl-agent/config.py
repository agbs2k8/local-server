import os
import sys


APP_NAME = os.getenv("APP_NAME", "trmnl-agent")
APP_VERSION = "0.0.1"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:5000/webhook")
SOURCE_URL = os.getenv("SOURCE_URL", "https://www.accuweather.com/en/us/lakeville/55044/sinus-weather/2247734")
PULL_RETRY = int(os.getenv("PULL_RETRY", "3"))

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