# YouTube Transcript Extractor Makefile

# Python interpreter
PYTHON := python3
PIP := pip3

# Virtual environment
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Project files
MAIN_FILE := main.py
REQUIREMENTS := requirements.txt

.PHONY: help install install-dev venv clean run lint format test setup dev

# Default target
help:
	@echo "Available targets:"
	@echo "  setup       - Create virtual environment and install dependencies"
	@echo "  install     - Install dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  venv        - Create virtual environment"
	@echo "  run         - Run the YouTube transcript extractor"
	@echo "  clean       - Remove virtual environment and cache files"
	@echo "  lint        - Run code linting (requires flake8)"
	@echo "  format      - Format code (requires black)"
	@echo "  test        - Run tests (requires pytest)"
	@echo "  dev         - Set up development environment"

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created at $(VENV)"

# Install dependencies
install: $(REQUIREMENTS)
	@echo "Installing dependencies..."
	$(PIP) install -r $(REQUIREMENTS)

# Install dependencies in virtual environment
install-venv: venv
	@echo "Installing dependencies in virtual environment..."
	$(VENV_PIP) install -r $(REQUIREMENTS)

# Install development dependencies
install-dev: install
	@echo "Installing development dependencies..."
	$(PIP) install flake8 black pytest pytest-cov

# Full setup (recommended for new users)
setup: venv install-venv
	@echo "Setup complete! Activate virtual environment with:"
	@echo "  source $(VENV_BIN)/activate"

# Run the application
run:
	$(VENV_PYTHON) $(MAIN_FILE)

# Development setup
dev: setup install-dev
	@echo "Development environment ready!"

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV)
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "Cleanup complete"

# Code linting
lint:
	@echo "Running code linting..."
	flake8 *.py --max-line-length=88 --ignore=E203,W503

# Code formatting
format:
	@echo "Formatting code..."
	black *.py

# Run tests
test:
	@echo "Running tests..."
	pytest -v

# Check if virtual environment exists
check-venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi