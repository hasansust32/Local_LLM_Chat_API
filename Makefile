.PHONY: dev test docker-up docker-down

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

docker-up:
	docker compose up --build

docker-down:
	docker compose down

