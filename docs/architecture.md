# LedgerFlow Architecture

LedgerFlow is a multi-tenant expense submission and approval platform. Organizations isolate their data in a shared PostgreSQL schema. Employees submit expenses, managers approve or reject them, administrators manage categories and budgets, and asynchronous workers produce CSV exports.

## System overview

```text
Client (HTTP/JSON)
        │
     Nginx (production)
        │
Django + Django REST Framework (Gunicorn)
        │
   ┌────┴────┐
PostgreSQL  Redis ── Celery worker
```

The application is deployed as a modular monolith: one Django codebase with clear domain apps (`accounts`, `expenses`, `approvals`, `budgets`, `reporting`, `audit`, `core`).

## Domain model

- **User / Organization / Membership** — identity and tenant membership with roles `owner`, `admin`, `manager`, `employee`.
- **Category / Expense / ExpenseAttachment** — expense lifecycle from `draft` → `submitted` → `approved` | `rejected` | `cancelled`.
- **ApprovalPolicy / ApprovalAction** — amount-based approval requirements and decision history.
- **Budget** — period limits; submitted and approved expenses consume capacity.
- **ExportJob** — Celery-backed CSV export status and artifact storage.
- **AuditEvent** — append-only record of sensitive business actions.

## Request flow

1. The client authenticates with JWT (`/api/v1/auth/token/`).
2. Tenant-scoped routes expect `Authorization: Bearer …` and, when the user belongs to multiple organizations, `X-Organization-ID`.
3. Permission classes resolve membership, attach `request.organization` / `request.membership`, and enforce role ranks.
4. Views validate input, call service-layer use cases, and return serializers.
5. Services encapsulate transactions (`select_for_update` on expense/budget paths), status transitions, budget checks, and audit writes.
6. Export endpoints enqueue Celery tasks that write CSV files under media storage.

## Boot sequence

1. Process starts with `DJANGO_SETTINGS_MODULE` selecting `local`, `test`, or `production`.
2. Settings load environment variables (`DATABASE_URL`, `REDIS_URL`, JWT lifetimes, CORS).
3. Django loads installed apps and middleware (CORS, auth, request ID, organization header capture).
4. `ledgerflow.config.celery` creates the Celery app and autodiscovers tasks.
5. Container entrypoint waits for PostgreSQL, runs migrations, then starts Gunicorn or the Celery worker.
6. Readiness (`/api/v1/ready/`) probes database and cache connectivity.

## Multi-tenancy

LedgerFlow uses a shared database and shared schema. Tenant rows carry `organization_id`. Querysets for tenant resources always filter by the resolved organization. Cross-tenant access returns HTTP 404 or 403.

## Technology choices

| Concern | Choice | Rationale |
|---|---|---|
| API framework | Django + DRF | Mature auth, admin, ORM, and permission ecosystem for SaaS |
| Auth | JWT (SimpleJWT) | Stateless API access suitable for SPA/mobile clients |
| Database | PostgreSQL | Constraints, JSON audit payloads, production default |
| Cache / broker | Redis | Response caching and Celery broker in a single dependency |
| Jobs | Celery | Standard Django background processing |
| Packaging | uv | Fast, reproducible lockfiles |
| Quality | Pytest, Ruff, coverage gates, GitHub Actions | CI-enforced baseline |

## API surface (v1)

- Auth: register, token, refresh, me
- Organizations and members
- Categories, expenses (CRUD draft, submit, cancel, attachments)
- Approve / reject, approval policies
- Budgets
- Report exports
- Health / ready
- OpenAPI schema at `/api/schema/` and Swagger UI at `/api/docs/`

## Operational topology

Development Compose runs `web`, `worker`, `db`, and `redis`. Production Compose adds Nginx, multi-stage images, health checks, and persistent volumes for PostgreSQL and media.
