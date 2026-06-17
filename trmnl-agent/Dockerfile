FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r trmnl && useradd -r -g trmnl trmnl

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy the package metadata and source before installing the app package
COPY pyproject.toml .
COPY app/ ./app/
COPY main.py .
COPY config.py .
# The --trusted-host options are added to ensure that pip can access the package index without SSL issues primarily from VPN problems
RUN pip install --no-cache-dir . --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org setuptools

# Create necessary directories and set permissions
RUN mkdir -p /app/logs && \
    chown -R trmnl:trmnl /app

# Switch to non-root user
USER trmnl

# Health check (remove since this isn't a web service)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8080/health || exit 1

# Default environment variables
ENV LOG_LEVEL=INFO \
    PYTHONPATH=/app

# Run the application
CMD ["python", "main.py"]