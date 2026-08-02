# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.6.17 /uv /usr/local/bin/uv

FROM base AS builder
COPY pyproject.toml README.md ./
COPY src ./src
COPY uv.lock* ./
RUN if [ -f uv.lock ]; then uv sync --frozen --no-dev; else uv sync --no-dev; fi

FROM base AS runtime
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R appuser:appuser /app
USER appuser
WORKDIR /app/src
ENV DJANGO_SETTINGS_MODULE=ledgerflow.config.settings.production \
    PYTHONPATH=/app/src
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/api/v1/health/ || exit 1
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "ledgerflow.config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
