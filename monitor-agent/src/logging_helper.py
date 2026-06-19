from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# Configure logging
logging.basicConfig(filename="app.log", level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        method = request.method
        url = request.url.path

        logger.info(f"Request: {method} {url} from {client_ip}")
        response = await call_next(request)
        logger.info(f"Response: {method} {url} returned {response.status_code} to {client_ip}")
        return response