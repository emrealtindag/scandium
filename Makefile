# =============================================================================
# Scandium - Production-Grade Precision Landing System
# Makefile
# =============================================================================
# This Makefile provides development workflow shortcuts.
# Usage: make <target>
# =============================================================================

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

.PHONY: all clean install install-dev lint format typecheck test test-unit \
        test-integration test-cov docs docs-serve build docker docker-compose \
        check ci pre-commit security audit sim-ardupilot sim-px4 sim-airsim \
        help version

# Default shell
SHELL := /bin/bash

# Python interpreter
PYTHON := python3

# Poetry command
POETRY := poetry

# Package name
PACKAGE := scandium

# Source directory
SRC_DIR := src/scandium

# Test directory
TEST_DIR := tests

# Documentation directory
DOCS_DIR := docs

# Docker image name
DOCKER_IMAGE := scandium

# Default target
.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Development Environment
# -----------------------------------------------------------------------------

## Install production dependencies
install:
	$(POETRY) install --only main

## Install all dependencies (dev, docs, sim)
install-dev:
	$(POETRY) install --with dev,docs
	$(POETRY) run pre-commit install

## Install pre-commit hooks
pre-commit:
	$(POETRY) run pre-commit install
	$(POETRY) run pre-commit run --all-files

# -----------------------------------------------------------------------------
# Code Quality
# -----------------------------------------------------------------------------

## Run all linting checks
lint:
	$(POETRY) run ruff check .
	$(POETRY) run black --check .

## Run code formatter
format:
	$(POETRY) run ruff check --fix .
	$(POETRY) run black .
	$(POETRY) run ruff format .

## Run static type checker
typecheck:
	$(POETRY) run mypy $(SRC_DIR)

## Run all quality checks (lint, format check, typecheck)
check: lint typecheck
	@echo "All quality checks passed."

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

## Run all tests
test:
	$(POETRY) run pytest $(TEST_DIR) -v

## Run unit tests only
test-unit:
	$(POETRY) run pytest $(TEST_DIR)/unit -v -m "unit or not (integration or slow or simulation)"

## Run integration tests only
test-integration:
	$(POETRY) run pytest $(TEST_DIR)/integration -v -m "integration"

## Run tests with coverage report
test-cov:
	$(POETRY) run pytest $(TEST_DIR) \
		--cov=$(SRC_DIR) \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=70
	@echo "Coverage report generated in htmlcov/index.html"

## Run smoke tests only
test-smoke:
	$(POETRY) run pytest $(TEST_DIR) -v -m "smoke"

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------

## Run security audit on dependencies
security:
	$(POETRY) run pip-audit

## Run all security checks
audit: security
	$(POETRY) run bandit -r $(SRC_DIR) -ll

# -----------------------------------------------------------------------------
# Documentation
# -----------------------------------------------------------------------------

## Build documentation
docs:
	$(POETRY) run mkdocs build --strict

## Serve documentation locally
docs-serve:
	$(POETRY) run mkdocs serve --dev-addr localhost:8000

# -----------------------------------------------------------------------------
# Build and Distribution
# -----------------------------------------------------------------------------

## Build Python package (wheel and sdist)
build:
	$(POETRY) build

## Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf site/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------

## Build Docker image
docker:
	docker build -f docker/Dockerfile -t $(DOCKER_IMAGE):dev .

## Build and run Docker Compose stack
docker-compose:
	docker compose -f docker/docker-compose.yml up --build

## Stop Docker Compose stack
docker-down:
	docker compose -f docker/docker-compose.yml down

# -----------------------------------------------------------------------------
# Simulation
# -----------------------------------------------------------------------------

## Start ArduPilot SITL
sim-ardupilot:
	./scripts/run_sitl_ardupilot.sh

## Start PX4 SITL
sim-px4:
	./scripts/run_sitl_px4.sh

## Run AirSim demo
sim-airsim:
	$(POETRY) run scandium sim airsim --config configs/airsim_demo.yaml

# -----------------------------------------------------------------------------
# CI/CD
# -----------------------------------------------------------------------------

## Run full CI pipeline locally
ci: clean install-dev lint typecheck test-cov security docs
	@echo "CI pipeline completed successfully."

# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------

## Show package version
version:
	$(POETRY) run scandium version

## Display this help message
help:
	@echo "Scandium - Production-Grade Precision Landing System"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Development Environment:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install all dependencies (dev, docs, sim)"
	@echo "  pre-commit       Install and run pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks (ruff, black)"
	@echo "  format           Run code formatters"
	@echo "  typecheck        Run static type checker (mypy)"
	@echo "  check            Run all quality checks"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-cov         Run tests with coverage report"
	@echo "  test-smoke       Run smoke tests only"
	@echo ""
	@echo "Security:"
	@echo "  security         Run dependency security audit"
	@echo "  audit            Run all security checks"
	@echo ""
	@echo "Documentation:"
	@echo "  docs             Build documentation"
	@echo "  docs-serve       Serve documentation locally"
	@echo ""
	@echo "Build and Distribution:"
	@echo "  build            Build Python package"
	@echo "  clean            Clean build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  docker           Build Docker image"
	@echo "  docker-compose   Run Docker Compose stack"
	@echo "  docker-down      Stop Docker Compose stack"
	@echo ""
	@echo "Simulation:"
	@echo "  sim-ardupilot    Start ArduPilot SITL"
	@echo "  sim-px4          Start PX4 SITL"
	@echo "  sim-airsim       Run AirSim demo"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci               Run full CI pipeline locally"
	@echo ""
	@echo "Utility:"
	@echo "  version          Show package version"
	@echo "  help             Display this help message"
