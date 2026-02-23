.PHONY: up down logs backend-test migrate start stop reset

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

backend-test:
	cd backend && pytest -q

migrate:
	docker compose run --rm backend alembic upgrade head

# One-command startup for evaluators and demo users.
start:
	docker compose up --build -d
	docker compose run --rm backend alembic upgrade head

# Stop containers but keep DB/vector volumes.
stop:
	docker compose down

# Full reset (including volumes).
reset:
	docker compose down -v
