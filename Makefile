.PHONY: install test lint format migrate run compose-up compose-down

install:
	uv sync --group dev

test:
	uv run pytest

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

migrate:
	cd src && uv run python manage.py migrate

run:
	cd src && uv run python manage.py runserver 0.0.0.0:8000

compose-up:
	docker compose up --build

compose-down:
	docker compose down -v
