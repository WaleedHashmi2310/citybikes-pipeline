# CityBikes Pipeline Makefile
# Author: Claude Code
# Date: 2026-03-24

.PHONY: help setup install test lint format clean ingest ingest-local ingest-networks generate-sample-data dbt-run dbt-test pipeline dbt-docs dbt-clean all docker-build docker-up docker-down docker-logs docker-init docker-airflow docker-stop docker-clean docker-resume env-setup check-env terraform-init terraform-plan terraform-apply terraform-destroy terraform-output terraform-fmt terraform-validate gcp-generate-env gcp-create-key local cloud cloud-destroy cloud-pipeline

# Variables
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
DBT = $(VENV)/bin/dbt
PROJECT_NAME = citybikes-pipeline
DBT_PROFILES_DIR = dbt/profiles
DBT_PROJECT_DIR = dbt
RAW_DATA_PATH = data/raw
TERRAFORM_DIR = terraform
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

setup:  ## Set up Python virtual environment and install all dependencies for pipeline
	@echo "Setting up virtual environment using Python 3.12..."
	python3.12 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[storage,dbt,dev]"

install: setup  ## Install the package in development mode (alias for setup)

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
	cd $(DBT_PROJECT_DIR) && $(DBT) clean --profiles-dir $(DBT_PROFILES_DIR)

ingest:  ## Run data ingestion (extract and store) using configured storage backend
	$(PYTHON) scripts/run_ingestion.py

ingest-local:  ## Run ingestion with local storage (Parquet files)
	STORAGE_BACKEND=local $(PYTHON) scripts/run_ingestion.py

ingest-networks:  ## Run ingestion with specific networks (set NETWORKS variable)
	STORAGE_BACKEND=local CITYBIKES_NETWORKS=$(NETWORKS) $(PYTHON) scripts/run_ingestion.py

generate-sample-data:  ## Generate sample Parquet data for testing
	$(PYTHON) scripts/generate_sample_data.py

dbt-run:  ## Run dbt models (requires installed dbt dependencies)
	$(DBT) run --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

dbt-test:  ## Run dbt data tests
	$(DBT) test --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

pipeline: ingest-local dbt-run dbt-test  ## Run local pipeline: ingestion -> dbt -> data tests

dbt-docs:  ## Generate dbt documentation
	$(DBT) docs generate --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

dbt-clean:  ## Clean dbt artifacts
	$(DBT) clean --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

all: install test dbt-run dbt-test  ## Run full pipeline: install, test, transform, test data

# Docker Airflow targets
docker-build:  ## Build Docker image for Airflow
	docker compose build

docker-up:  ## Start Airflow with Docker Compose
	docker compose up -d postgres airflow-webserver airflow-scheduler

docker-down:  ## Stop Airflow Docker Compose services
	docker compose down

docker-logs:  ## View Airflow Docker Compose logs
	docker compose logs -f

docker-init:  ## Initialize Airflow database (one-time setup)
	docker compose up airflow-init

docker-airflow: docker-build docker-init docker-up  ## Build, initialize, and start Airflow with Docker

docker-stop:  ## Gracefully stop Airflow containers (without removing)
	docker compose stop

docker-clean:  ## Completely remove Airflow containers, networks, and volumes
	docker compose down -v --remove-orphans

docker-resume:  ## Resume previously stopped Airflow containers
	docker compose start

# GCP deployment utilities
gcp-generate-env:  ## Generate environment variables for GCP from Terraform outputs
	python scripts/generate_gcp_env.py --format bash

gcp-create-key:  ## Create GCP service account key for authentication
	python scripts/create_service_account_key.py

# Terraform infrastructure targets
terraform-init:  ## Initialize Terraform working directory
	cd $(TERRAFORM_DIR) && terraform init

terraform-plan:  ## Generate Terraform execution plan
	cd $(TERRAFORM_DIR) && terraform plan -var-file=terraform.tfvars

terraform-apply:  ## Apply Terraform changes
	cd $(TERRAFORM_DIR) && terraform apply -var-file=terraform.tfvars -auto-approve

terraform-destroy:  ## Destroy Terraform-managed infrastructure
	cd $(TERRAFORM_DIR) && terraform destroy -var-file=terraform.tfvars -auto-approve

terraform-output:  ## Show Terraform output values
	cd $(TERRAFORM_DIR) && terraform output

terraform-fmt:  ## Format Terraform configuration files
	cd $(TERRAFORM_DIR) && terraform fmt -recursive

terraform-validate:  ## Validate Terraform configuration
	cd $(TERRAFORM_DIR) && terraform validate

# High-level orchestration targets
local: setup docker-airflow  ## Set up local environment and start Airflow with Docker

cloud: setup terraform-init terraform-apply gcp-create-key gcp-generate-env  ## Deploy to GCP: provision infrastructure, create service account key, start Airflow VM

cloud-destroy: terraform-destroy  ## Destroy all GCP resources

cloud-pipeline:  ## Run pipeline directly in cloud mode (requires GCP credentials set)
	@if [ -f .env ]; then \
		set -a; \
		source .env; \
		set +a; \
		echo "Sourced environment from .env file"; \
	fi; \
	STORAGE_BACKEND=gcs DBT_TARGET=prod $(PYTHON) scripts/run_ingestion.py; \
	DBT_TARGET=prod $(DBT) run --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR); \
	DBT_TARGET=prod $(DBT) test --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR)

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