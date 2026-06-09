# Prato do Dia API

Backend API for the UERJ Prato do Dia university research prototype.

This repository currently contains a minimal FastAPI foundation for the mobile
app. It has no web frontend and no authentication.

## Stack

- Python 3.12
- uv
- FastAPI
- SQLite
- SQLAlchemy
- Alembic
- Pydantic Settings
- pytest
- ruff
- basedpyright
- pre-commit

## Setup

Install Python 3.12 with uv:

```bash
uv python install 3.12
```

Create the environment and install dependencies:

```bash
uv sync
```

Run the API (listening on all interfaces using the random port `42917` to allow local mobile connections):

```bash
uv run uvicorn prato_do_dia_api.main:app --host 0.0.0.0 --port 42917 --reload
```

## Endpoints

- `GET /` returns `{ "message": "Prato do Dia API" }`
- `GET /health` returns `{ "status": "ok", "service": "prato-do-dia-api" }`

## Quality Commands

Run tests:

```bash
uv run pytest
```

Run lint:

```bash
uv run ruff check .
```

Run format:

```bash
uv run ruff format .
```

Run type check:

```bash
uv run basedpyright
```

Install pre-commit:

```bash
uv run pre-commit install
```

Run all pre-commit hooks:

```bash
uv run pre-commit run --all-files
```

## Configuration

Copy `.env.example` to `.env` for local overrides when needed. The default
database URL is:

```text
sqlite:///./data/prato_do_dia.db
```

