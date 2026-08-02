# LedgerFlow

LedgerFlow is a multi-tenant expense submission and approval API built with Django and Django REST Framework. Organizations manage categories, budgets, and approval policies; employees submit expenses with optional receipts; managers approve or reject claims; and CSV exports run through Celery workers.

The project is designed as a production-shaped modular monolith: JWT authentication, tenant isolation, role-based access, transactional budget checks, audit logging, Docker Compose, and CI.

## What was built

- User registration and JWT authentication (access + refresh)
- Organizations and memberships with roles: `owner`, `admin`, `manager`, `employee`
- Expense lifecycle: `draft` → `submitted` → `approved` / `rejected` / `cancelled`
- Budget enforcement on submit (submitted + approved amounts consume capacity)
- Approval decisions with audit events
- Asynchronous CSV export jobs via Celery + Redis
- OpenAPI schema and Swagger UI
- Pytest suite covering tenancy, permissions, budgets, and exports
- Docker development and production Compose stacks with Nginx
- GitHub Actions workflows for lint, test, and image build

## Technologies and why they were chosen

| Technology | Role | Why |
|---|---|---|
| Python 3.12 | Runtime | Modern typing and ecosystem compatibility |
| Django 5 | Web framework | Strong ORM, auth, admin, and SaaS patterns |
| Django REST Framework | HTTP API | Serializers, permissions, throttling, browsable tooling |
| SimpleJWT | Auth | Stateless API authentication for SPA/mobile clients |
| PostgreSQL | Primary data store | Relational integrity and production default for SaaS |
| Redis | Cache + Celery broker | Simple local topology; cache and queue in one dependency |
| Celery | Background jobs | Standard Django worker model for exports |
| Gunicorn + Nginx | App server + reverse proxy | Common production deployment pattern |
| Docker / Compose | Runtime packaging | Reproducible local and VPS-style deployments |
| uv | Packaging | Fast installs and lockfile reproducibility |
| Pytest + factory_boy | Testing | API/unit coverage with realistic fixtures |
| Ruff | Lint/format | Fast single-tool quality gate |
| drf-spectacular | OpenAPI | Generated API documentation |
| GitHub Actions | CI | Automated lint, test, and Docker build |

## What this project demonstrates

- Shared-schema multi-tenancy and cross-tenant isolation testing
- Service-layer domain workflows instead of fat views
- Budget concurrency considerations with row locking
- Separating synchronous API work from asynchronous reporting
- Configuration via environment variables across local/test/production
- Containerized web + worker + Postgres + Redis topology

## Architecture

See [docs/architecture.md](docs/architecture.md) for system context, domain model, request flow, and boot sequence.

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker and Docker Compose (recommended)
- Git

## Quick start (Docker Compose)

This is the recommended local path. It starts PostgreSQL, Redis, the API, and the Celery worker together.

```bash
git clone https://github.com/EduardoFernandess/ledgerflow.git
cd ledgerflow
cp .env.example .env
docker compose up --build
```

When healthy:

- API: http://localhost:8000/api/v1/health/
- Swagger UI: http://localhost:8000/api/docs/
- OpenAPI schema: http://localhost:8000/api/schema/

Stop and remove volumes:

```bash
docker compose down -v
```

## Local run without full Compose (API on the host)

Use this when iterating on Python code with dependencies managed by `uv`. Postgres and Redis can still run in Docker.

### 1. Clone and install

```bash
git clone https://github.com/EduardoFernandess/ledgerflow.git
cd ledgerflow
cp .env.example .env
uv sync --group dev
```

### 2. Start Postgres and Redis

```bash
docker compose up -d db redis
```

### 3. Point env at local services

Edit `.env` so host-side processes reach published ports:

```env
DEBUG=True
SECRET_KEY=dev-only-change-me-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://ledgerflow:ledgerflow@127.0.0.1:5432/ledgerflow
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
DJANGO_SETTINGS_MODULE=ledgerflow.config.settings.local
```

### 4. Migrate and run the API

```bash
cd src
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

### 5. Run the worker (second terminal)

```bash
cd src
uv run celery -A ledgerflow.config.celery worker --loglevel=INFO
```

### SQLite fallback (tests / quick experiments)

Tests use in-memory SQLite automatically via `ledgerflow.config.settings.test`. For a no-Docker smoke run, unset `DATABASE_URL` and use the default SQLite file from settings, understanding that Redis-backed cache may fall back to LocMem in `local` settings when Redis is unavailable.

## Demo API flow

```bash
# Register (creates user + organization)
curl -s -X POST http://localhost:8000/api/v1/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com","password":"password123","full_name":"Owner","organization_name":"Acme"}'

# Obtain JWT
curl -s -X POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com","password":"password123"}'
```

Use the access token as `Authorization: Bearer <token>`. If the user belongs to multiple organizations, also send `X-Organization-ID: <org-uuid>`.

Typical sequence:

1. `POST /api/v1/categories/` with `{"name":"Travel"}`
2. `POST /api/v1/budgets/` with period + `limit_amount`
3. `POST /api/v1/expenses/` then `POST /api/v1/expenses/{id}/submit/`
4. `POST /api/v1/expenses/{id}/approve/` as a manager/admin/owner
5. `POST /api/v1/reports/exports/` and poll `GET /api/v1/reports/exports/{id}/`

## Tests

```bash
uv sync --group dev
uv run pytest
```

## Lint / format

```bash
uv run ruff check src tests
uv run ruff format src tests
```

## Makefile helpers

```bash
make install
make test
make lint
make compose-up
make compose-down
```

## Production-oriented Compose

```bash
export POSTGRES_PASSWORD=choose-a-strong-password
export SECRET_KEY=choose-a-long-random-secret
export DATABASE_URL=postgres://ledgerflow:${POSTGRES_PASSWORD}@db:5432/ledgerflow
export REDIS_URL=redis://redis:6379/0
export CELERY_BROKER_URL=redis://redis:6379/1
export CELERY_RESULT_BACKEND=redis://redis:6379/2
export ALLOWED_HOSTS=your.domain,localhost
export CORS_ALLOWED_ORIGINS=https://your.frontend

docker compose -f docker-compose.prod.yml up --build -d
```

Nginx listens on port 80 and proxies to Gunicorn.

## Deployment notes

The same containerized shape maps to:

- **Docker VPS:** run `docker-compose.prod.yml` behind TLS (Caddy/Nginx) and managed backups for the Postgres volume.
- **Railway / Render:** one web service + one worker service, managed Postgres/Redis add-ons, env vars from `.env.example`.
- **DigitalOcean App Platform:** similar web/worker split with a managed database.
- **AWS:** ECS/Fargate or EC2 for web/worker, RDS Postgres, ElastiCache Redis, S3 for media in a later iteration.

Details: [docs/deployment.md](docs/deployment.md).

## Project layout

```text
ledgerflow/
├── docker/                 # Dockerfile + Nginx config
├── docs/                   # Architecture and deployment
├── src/ledgerflow/         # Django project and domain apps
├── tests/                  # API and unit tests
├── docker-compose.yml      # Development stack
├── docker-compose.prod.yml # Production-oriented stack
├── pyproject.toml          # Dependencies and tool config
└── .github/workflows/      # CI
```

## Known limitations

- Managers are organization-wide (no team graph)
- No multi-currency conversion
- Attachments/exports use filesystem/volume storage by default
- Redis is used as the Celery broker in this project

## License

MIT
