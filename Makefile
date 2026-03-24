# CityBikes Pipeline Makefile
# Author: Claude Code
# Date: 2026-03-24

.PHONY: help setup install install-dev install-dbt install-storage install-airflow test lint format clean ingest ingest-local ingest-networks generate-sample-data dbt-run dbt-test dbt-docs dbt-clean all pipeline

# Variables
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PROJECT_NAME = citybikes-pipeline
DBT_PROFILES_DIR = dbt/profiles
DBT_PROJECT_DIR = dbt
RAW_DATA_PATH = data/raw
NETWORKS ?= callabike-frankfurt,visa-frankfurt,callabike-koln,kvb-rad-koln,nextbike-dusseldorf,stadtrad-hamburg-db,callabike-munchen,stadtrad-stuttgart,mobibike-dresden,nextbike-leipzig,callabike-berlin,mvg-meinrad-nextbike-mainz

# Determine OS for activate script
ifeq ($(OS),Windows_NT)
	ACTIVATE = $(VENV)/Scripts/activate
else
	ACTIVATE = . $(VENV)/bin/activate
endif

help:  ## Show this help message
	@echo "CityBikes Pipeline - Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Set up Python virtual environment and install base dependencies
	@echo "Setting up virtual environment using Python 3.12..."
	python3.12 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .

install: setup  ## Install the package in development mode (alias for setup)

install-dev:  ## Install development dependencies
	$(PIP) install -e ".[dev]"

install-storage:  ## Install storage dependencies (GCS, DuckDB)
	$(PIP) install -e ".[storage]"

install-dbt:  ## Install dbt dependencies
	$(PIP) install -e ".[dbt]"

install-airflow:  ## Install Apache Airflow dependencies
	$(PIP) install -e ".[airflow]"

install-all: install install-dev install-storage install-dbt install-airflow  ## Install all dependencies

test:  ## Run unit tests with pytest
	$(PYTHON) -m pytest tests/ -v --cov=ingestion --cov=storage --cov-report=term-missing

lint:  ## Run flake8 linter
	$(PYTHON) -m flake8 ingestion/ storage/ tests/ scripts/ --count --show-source --statistics

format:  ## Format code with black and isort
	$(PYTHON) -m black ingestion/ storage/ tests/ scripts/
	$(PYTHON) -m isort ingestion/ storage/ tests/ scripts/

clean:  ## Remove generated files and virtual environment
	@echo "Cleaning up..."
	rm -rf $(VENV)
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov
	rm -rf data/raw/* data/processed/*
	rm -f citybikes.duckdb
	cd $(DBT_PROJECT_DIR) && dbt clean --profiles-dir $(DBT_PROFILES_DIR)

ingest:  ## Run data ingestion (extract and store) using configured storage backend
	$(PYTHON) scripts/run_ingestion.py

ingest-local:  ## Run ingestion with local storage (Parquet files)
	STORAGE_BACKEND=local $(PYTHON) scripts/run_ingestion.py

ingest-networks:  ## Run ingestion with specific networks (set NETWORKS variable)
	STORAGE_BACKEND=local CITYBIKES_NETWORKS=$(NETWORKS) $(PYTHON) scripts/run_ingestion.py

generate-sample-data:  ## Generate sample Parquet data for testing
	$(PYTHON) scripts/generate_sample_data.py

dbt-run:  ## Run dbt models (requires installed dbt dependencies)
	dbt run --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

dbt-test:  ## Run dbt data tests
	dbt test --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

pipeline: ingest-local dbt-run dbt-test  ## Run local pipeline: ingestion -> dbt -> data tests

dbt-docs:  ## Generate dbt documentation
	dbt docs generate --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

dbt-clean:  ## Clean dbt artifacts
	dbt clean --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

all: install-all test dbt-run dbt-test  ## Run full pipeline: install, test, transform, test data

# Shortcut targets
venv: setup
dev: install-dev
storage: install-storage
dbt: install-dbt dbt-run
airflow: install-airflow

# Environment setup reminder
env-setup:  ## Copy environment template and remind about configuration
	@echo "Copying environment template..."
	cp .env.example .env
	@echo "\nPlease edit .env file with your configuration."
	@echo "For local development with DuckDB, set DBT_DUCKDB_PATH (default: citybikes.duckdb)"
	@echo "For cloud deployment, set BigQuery and GCS variables.\n"

# Check environment
check-env:  ## Check if required environment variables are set
	@echo "Checking environment..."
	@if [ -f ".env" ]; then \
		echo ".env file exists."; \
	else \
		echo "WARNING: .env file not found. Run 'make env-setup' first."; \
	fi
	@echo "Current DBT_DUCKDB_PATH: $(DBT_DUCKDB_PATH)"