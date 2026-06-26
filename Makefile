.PHONY: install dev build test docker-up docker-down clean

install:
	pip install -r requirements.txt
	cd frontend && npm install

dev:
	./scripts/dev.sh

build:
	docker-compose build

test:
	pytest
	cd frontend && npm test

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	docker-compose down -v
	rm -rf __pycache__ .pytest_cache .mypy_cache
	cd frontend && rm -rf node_modules dist