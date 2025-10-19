.PHONY: install dev test lint format clean docker-up docker-down eval agent interactive help venv sync

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv: ## Create virtual environment with uv
	uv venv

sync: ## Sync dependencies from lock file (fast)
	uv sync --all-extras

install: ## Install package in production mode
	uv pip install -e .

dev: venv ## Install package with development dependencies
	uv pip install -e ".[dev]"

test: ## Run tests with coverage
	uv run pytest --cov=src/agent_sdk --cov-report=html --cov-report=term-missing

test-fast: ## Run tests without coverage
	uv run pytest -v

lint: ## Run linting checks
	uv run ruff check src/ tests/ examples/
	uv run mypy src/

format: ## Format code with black and ruff
	uv run black src/ tests/ examples/
	uv run ruff check --fix src/ tests/ examples/

clean: ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .venv/
	rm -rf uv.lock
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-up: ## Start Langfuse services
	docker compose up -d
	@echo "Waiting for Langfuse to be ready..."
	@sleep 5
	@echo "Langfuse should be available at http://localhost:3200"

docker-down: ## Stop Langfuse services
	docker compose down

docker-logs: ## Show Langfuse logs
	docker compose logs -f

eval: ## Run evaluation on test dataset
	uv run python examples/run_evaluation.py

agent: ## Run simple agent demo
	uv run python examples/run_agent.py

interactive: ## Start interactive agent session
	uv run python examples/interactive_agent.py

setup: dev docker-up ## Complete setup: install dependencies and start Langfuse
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "1. Go to http://localhost:3200 and create a Langfuse account"
	@echo "2. Create a project and get your API keys"
	@echo "3. Copy .env.example to .env and add your keys"
	@echo "4. Run 'make agent' to test the setup"
