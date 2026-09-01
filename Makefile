# ============================================================
# Sentinel — Makefile
# ============================================================

.PHONY: help setup dev test lint clean docker-up docker-down

help:
	@echo "Sentinel — AI-Powered Payment Risk Control Tower"
	@echo ""
	@echo "Usage:"
	@echo "  make setup        Install all dependencies"
	@echo "  make dev          Start development servers"
	@echo "  make test         Run all tests"
	@echo "  make lint         Run linters"
	@echo "  make docker-up    Start Docker Compose stack"
	@echo "  make docker-down  Stop Docker Compose stack"
	@echo "  make download-data Download Kaggle dataset"
	@echo "  make train        Train ML model"
	@echo "  make seed         Seed database with demo data"
	@echo "  make clean        Remove generated artifacts"

setup:
	@echo "→ Setting up backend..."
	cd backend && pip install -r requirements.txt
	@echo "→ Setting up ML pipeline..."
	cd ml && pip install -r requirements.txt
	@echo "→ Setting up frontend..."
	cd frontend && npm install
	@echo "✓ Setup complete"

dev:
	@echo "→ Start Docker (postgres) first with: make docker-up"
	@echo "→ Then run backend: cd backend && uvicorn app.main:app --reload"
	@echo "→ Then run frontend: cd frontend && npm run dev"

test:
	@echo "→ Running backend tests..."
	cd backend && pytest tests/ -v
	@echo "→ Running frontend tests..."
	cd frontend && npm run test

lint:
	@echo "→ Linting backend..."
	cd backend && ruff check app/ tests/
	@echo "→ Formatting check..."
	cd backend && black --check app/ tests/
	@echo "→ Linting frontend..."
	cd frontend && npm run lint

docker-up:
	docker compose up -d postgres
	@echo "✓ PostgreSQL running on localhost:5432"

docker-down:
	docker compose down

docker-build:
	docker compose up --build

download-data:
	python scripts/download_dataset.py

train:
	python scripts/train_model.py

seed:
	python scripts/seed_database.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned"
