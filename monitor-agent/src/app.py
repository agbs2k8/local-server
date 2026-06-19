import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI
# Imports from within the project
from config import cfg
from src.routes import router
from src.logging_helper import LoggingMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title=cfg.APP_NAME
    )
    
    # Routes
    app.include_router(router)

    # Logging Middleware
    app.add_middleware(LoggingMiddleware)
    
    return app