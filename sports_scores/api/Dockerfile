FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATA_DIR=/app/data \
    LOG_LEVEL=INFO

RUN groupadd -r sports && useradd -r -g sports sports

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG PIP_INSTALL_ARGS=""

COPY shared_models /build/shared_models
COPY api /build/api

RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org setuptools /build/shared_models /build/api && \
    rm -rf /build && \
    mkdir -p /app/data && \
    chown -R sports:sports /app

USER sports

EXPOSE 8000

CMD ["uvicorn", "src.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]