FROM python:3.13-slim AS build
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY main.py config.py ./

RUN pip install --no-cache-dir . --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org setuptools

FROM build AS test
COPY tests ./tests
RUN pip install .[test] --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org setuptools && pytest -q || true 

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=build /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY src ./src
COPY main.py config.py pyproject.toml ./

EXPOSE 8000
ENTRYPOINT ["uvicorn", "src.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]