# Shared Models

This package is now split into two layers so the FastAPI app and a future update job can share the same code cleanly:

- `shared_models.models` contains Pydantic models used for API responses, ingestion payloads, and in-process data transformations.
- `shared_models.db` contains SQLAlchemy ORM models, metadata, engine/session helpers, and the database bootstrap entrypoints.

## Main Types

- `League`, `Team`, and `Event` are the shared Pydantic models.
- `LeagueRecord`, `TeamRecord`, and `EventRecord` are the SQLAlchemy ORM tables.

## Alembic

Alembic is scaffolded at the `sports_scores` repo root and targets the shared SQLAlchemy metadata in `shared_models.db.Base.metadata`.

Typical commands:

```sh
cd /Users/ajwilson/GitRepos/local-server/sports_scores
alembic revision --autogenerate -m "create initial sports tables"
alembic upgrade head
```

By default the DB URL comes from `DATABASE_URL`. If it is unset, the shared package falls back to a local PostgreSQL default in `shared_models.db`.