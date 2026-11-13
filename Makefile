.PHONY: all up down logs ps clean re

all: up

up: .env
	docker compose up -d --build

.env:
	@echo "Missing .env - run: cp .env.example .env" && exit 1

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v --rmi local

re: clean up