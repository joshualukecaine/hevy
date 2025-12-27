.PHONY: help install install-dev lint format typecheck test test-cov clean build

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install the package with dev dependencies
	pip install -e ".[dev]"

lint:  ## Run linting checks
	ruff check src/ tests/
	ruff format --check src/ tests/

format:  ## Format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck:  ## Run type checking
	mypy src/hevy --ignore-missing-imports

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=hevy --cov-report=html --cov-report=term-missing

clean:  ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build:  ## Build the package
	python -m build

fetch:  ## Fetch exercise templates from Hevy
	python -m hevy.cli.fetch_templates

validate:  ## Validate a routine file (usage: make validate FILE=path/to/routine.json)
	python -m hevy.cli.create_routine --input $(FILE) --validate-only
