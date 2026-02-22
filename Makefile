.PHONY: up down logs backend-test migrate

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
