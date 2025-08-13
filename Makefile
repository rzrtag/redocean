# Red Ocean - MLB Analytics Platform
# Makefile for common operations

.PHONY: help install setup clean test lint format docs build run

# Default target
help:
	@echo "Red Ocean - MLB Analytics Platform"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  setup       - Set up environment and directories"
	@echo "  clean       - Clean build artifacts and cache"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  docs        - Generate documentation"
	@echo "  build       - Build the project"
	@echo "  run         - Run main application"
	@echo "  mlb-collect - Collect MLB data"
	@echo "  sabersim    - Run SaberSim analysis"
	@echo ""

# Environment setup
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

setup:
	@echo "Setting up environment..."
	mkdir -p _data/mlb_api_2025/{active_rosters,rolling_windows,statcast_adv_box}
	mkdir -p _data/sabersim_2025/{draftkings,fanduel}
	mkdir -p src/mlb_api/{rolling,rosters,shared,statcast_adv_box}
	mkdir -p src/sabersim/{atoms/{chunkers,extractors},tables}
	@echo "Environment setup complete!"

# Development
clean:
	@echo "Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage
	@echo "Clean complete!"

test:
	@echo "Running tests..."
	python -m pytest tests/ -v

lint:
	@echo "Running linting..."
	flake8 src/ tests/
	pylint src/ tests/

format:
	@echo "Formatting code..."
	black src/ tests/
	isort src/ tests/

docs:
	@echo "Generating documentation..."
	pdoc --html src/ --output-dir docs/

# Data collection
mlb-collect:
	@echo "Collecting MLB data..."
	python -m src.mlb_api.statcast_adv_box.cli collect
	python -m src.mlb_api.rosters.refresh_rosters
	python -m src.mlb_api.rolling.main

sabersim:
	@echo "Running SaberSim analysis..."
	python -m src.sabersim.atoms.main

# Main application
build:
	@echo "Building project..."
	python setup.py build

run:
	@echo "Running main application..."
	python -m src.main

# Quick development commands
dev-setup: setup install
	@echo "Development environment ready!"

quick-test: clean test
	@echo "Quick test complete!"

# Data management
data-clean:
	@echo "Cleaning data directories..."
	rm -rf _data/mlb_api_2025/cache/*
	rm -rf _data/sabersim_2025/cache/*

data-backup:
	@echo "Creating data backup..."
	tar -czf "backup_$(date +%Y%m%d_%H%M%S).tar.gz" _data/

# Environment management
env-activate:
	@echo "To activate environment, run:"
	@echo "conda activate red_ocean"

env-deactivate:
	@echo "To deactivate environment, run:"
	@echo "conda deactivate"

# Helpers
status:
	@echo "Project status:"
	@echo "Python version: $(shell python --version)"
	@echo "Environment: $(shell echo $$CONDA_DEFAULT_ENV)"
	@echo "Working directory: $(shell pwd)"
