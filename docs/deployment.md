# Deployment

LedgerFlow runs as two application processes (web + Celery worker) plus PostgreSQL and Redis.

## Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret |
| `DEBUG` | Must be `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hosts |
| `DATABASE_URL` | Postgres URL |
| `REDIS_URL` | Cache URL |
| `CELERY_BROKER_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | Celery results |
| `CORS_ALLOWED_ORIGINS` | Browser origins |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access lifetime |
| `REFRESH_TOKEN_LIFETIME_DAYS` | JWT refresh lifetime |

## Docker VPS

1. Install Docker.
2. Copy `.env.example` to `.env` and set strong secrets.
3. `docker compose -f docker-compose.prod.yml up --build -d`
4. Terminate TLS at a host proxy pointing at Nginx port 80/443.
5. Schedule Postgres volume backups.

## Railway / Render

- Provision Postgres and Redis.
- Deploy the web service with `gunicorn ledgerflow.config.wsgi:application`.
- Deploy a second service with `celery -A ledgerflow.config.celery worker --loglevel=INFO`.
- Run migrations as a release command: `python manage.py migrate`.

## DigitalOcean

Use App Platform (web + worker + managed DB) or a Droplet running the production Compose file.

## AWS

- **Compute:** ECS/Fargate services for web and worker, or EC2 with Compose.
- **Data:** RDS for PostgreSQL, ElastiCache for Redis.
- **Files:** move media to S3 by swapping Django storage backend.
- **Edge:** Application Load Balancer + HTTPS certificates.

## Production considerations

- Keep JWT access tokens short-lived.
- Do not commit `.env`.
- Monitor `/api/v1/ready/` for dependency health.
- Scale workers horizontally before scaling web if exports dominate CPU.
- Enable database backups and media volume snapshots before accepting real receipts.
