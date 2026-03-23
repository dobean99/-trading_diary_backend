# Repository Guidelines

## Project Structure & Module Organization
Core application code is in `app/`:
- `app/main.py`: FastAPI entrypoint.
- `app/api/`: route registration and versioned endpoints (`api/v1`).
- `app/models/`: SQLAlchemy models (`User`, `Trade`).
- `app/schemas/`: Pydantic request/response schemas.
- `app/db/`: SQLAlchemy base/session setup.
- `app/core/`: config, security, Celery, Redis clients.
- `app/services/`: async/background task logic.

Database migrations live in `alembic/` with revision files under `alembic/versions/`. Container orchestration is defined in `docker-compose.yml`.

## Build, Test, and Development Commands
- `docker compose up --build`: start API, Postgres, Redis, Celery worker, and beat.
- `docker compose run --rm api alembic upgrade head`: apply all migrations.
- `docker compose run --rm api alembic revision --autogenerate -m "message"`: create a new migration.
- `docker compose run --rm worker celery -A app.core.celery_app:celery_app worker -l info`: run worker manually.
- `docker compose logs -f api`: stream API logs during development.

## Coding Style & Naming Conventions
Use Python 3.13 style with PEP 8 defaults:
- 4-space indentation, `snake_case` for functions/variables/modules.
- `PascalCase` for classes and schema/model names.
- Keep route handlers thin; move business logic to `services/`.
- Keep environment/config keys uppercase in `.env` and mirrored in `app/core/config.py`.

Type hints are expected for new functions and model fields.

## Testing Guidelines
No formal test suite is currently committed. For new features:
- Add `pytest` tests under `tests/` using `test_*.py` naming.
- Cover API behavior, validation, and DB persistence paths.
- Run with `pytest -q` (inside the API container if dependencies are containerized).

## Commit & Pull Request Guidelines
Git history is not available in this workspace snapshot, so use this convention:
- Commit format: `type(scope): short summary` (example: `feat(auth): add refresh token endpoint`).
- Keep commits focused and migration changes isolated when possible.
- PRs should include: purpose, key changes, migration impact, manual verification steps, and sample API requests/responses for endpoint changes.

## Security & Configuration Tips
- Never commit real secrets; use `.env` (see `.env.example`).
- Rotate `JWT_SECRET_KEY` outside development.
- Validate migration scripts before applying in shared environments.
