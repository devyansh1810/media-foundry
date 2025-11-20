.PHONY: help install install-dev run test lint format clean docker-build docker-run docker-stop

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make install-dev   - Install dev dependencies"
	@echo "  make run           - Run the service locally"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean temporary files"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run with Docker Compose"
	@echo "  make docker-stop   - Stop Docker containers"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

run:
	python -m src.main

test:
	pytest -v --cov=src --cov-report=term-missing

lint:
	mypy src/
	ruff check src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf dist/ build/ *.egg-info/
	rm -f .coverage

docker-build:
	docker build -t ffmpeg-websocket-service:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f
