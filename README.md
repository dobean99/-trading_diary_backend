# trading-diary-backend

Backend starter for a trading diary system using:
- FastAPI
- PostgreSQL
- SQLAlchemy Async
- Alembic
- Redis
- Celery
- Docker Compose

## Quick Start

1. Copy env file:

```bash
cp .env.example .env
```

2. Start all services:

```bash
docker compose up --build
```

3. Open API docs:

- http://localhost:18081/docs

## Services

- API: `http://localhost:18081`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Useful Commands

Create migration:

```bash
docker compose run --rm api alembic revision --autogenerate -m "message"
```

Apply migration:

```bash
docker compose run --rm api alembic upgrade head
```

Run worker manually:

```bash
docker compose run --rm worker celery -A app.core.celery_app:celery_app worker -l info
```

## Auth API

Default seeded user:
- username: `admin`
- password: `admin123`

Endpoints:
- `POST /api/v1/auth/users`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout` (requires `Authorization: Bearer <token>`)
