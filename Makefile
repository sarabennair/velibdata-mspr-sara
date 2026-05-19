.PHONY: setup test lint format ingest clean help

help: ## Affiche cette aide
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Setup complet (uv + deps + pre-commit + .env)
uv sync --all-extras
uv run pre-commit install
@test -f .env || cp .env.example .env
@echo "Setup termine. Edite .env avec tes credentials."

test: ## Lance les tests
uv run pytest

lint: ## Verifie le code avec ruff
uv run ruff check src/ tests/

format: ## Formate le code avec ruff
uv run ruff format src/ tests/

ingest: ## Lance un cycle d ingestion
uv run python -m src.ingestion.main

clean: ## Nettoie les caches
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
rm -f .coverage
