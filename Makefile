.PHONY: help install dev test lint format clean docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	pytest tests/ -v

lint: ## Run linter
	ruff check app/ tests/
	mypy app/

format: ## Format code
	black app/ tests/
	ruff check app/ tests/ --fix

clean: ## Clean cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-up: ## Start services with docker-compose
	docker-compose up -d

docker-down: ## Stop services
	docker-compose down

docker-logs: ## Show logs
	docker-compose logs -f

docker-build: ## Build docker image
	docker-compose build

db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback last migration
	alembic downgrade -1

setup: ## Initial setup
	cp .env.example .env
	@echo "✅ Created .env file. Please edit it with your API keys."
	@echo "📝 Next steps:"
	@echo "   1. Edit .env file with your API keys"
	@echo "   2. Run 'make docker-up' to start services"
	@echo "   3. Visit http://localhost:8000" 