.DEFAULT_GOAL := help
CODE := src/app tests

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: ## Initialize local environment
	make install
	cp .env.local .env

.PHONY: install
install: ## Install dependencies
	uv sync

.PHONY: test
test: ## Runs pytest with coverage
	uv run pytest --cov=./

.PHONY: test-unit
test-unit: ## Runs unit tests only
	uv run pytest tests/unit

.PHONY: test-fast
test-fast: ## Runs pytest with exitfirst
	uv run pytest --exitfirst

.PHONY: test-failed
test-failed: ## Runs pytest from last-failed
	uv run pytest --last-failed

.PHONY: test-cov
test-cov: ## Runs pytest with coverage report
	uv run pytest --cov=./ --cov-report html

.PHONY: lint
lint: ## Lint code
	uv run ruff check $(CODE)
	uv run mypy $(CODE)
	uv run pytest --dead-fixtures --dup-fixtures

.PHONY: format
format: ## Formats all files
	uv run ruff check --fix-only $(CODE)
	uv run ruff format $(CODE)

.PHONY: check
check: format lint test ## Format and lint code then run tests

.PHONY: ci
ci: lint ## Lint code (tests run separately)

.PHONY: api
api: uv run api ## Run FastAPI server locally