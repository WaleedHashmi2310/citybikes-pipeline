# structure.md

## Repository Structure

```
project_root/
│
├── ingestion/              # API client, schemas, extraction logic
│   ├── client.py           # HTTP client for CityBikes API with retries
│   ├── schemas.py          # Pydantic schemas for data validation
│   ├── extractor.py        # Data extraction and transformation
│   ├── loader.py           # Orchestrates extraction and storage
│   └── utils.py            # Utility functions and helpers
│
├── storage/                # Storage abstraction (local Parquet / GCS)
│   ├── interface.py        # Abstract storage interface
│   ├── local.py            # Local filesystem storage implementation
│   └── gcs.py              # Google Cloud Storage implementation
│
├── warehouse/              # Warehouse-specific configurations
│   ├── duckdb/             # DuckDB warehouse utilities (placeholder)
│   └── bigquery/           # BigQuery warehouse utilities (placeholder)
│
├── dbt/                    # dbt transformations for data modeling
│   ├── dbt_project.yml     # dbt project configuration
│   ├── macros/             # Reusable SQL macros
│   │   ├── create_external_raw_data.sql  # Macro for creating BigQuery external table
│   │   └── get_raw_data.sql              # Macro for raw data access (DuckDB vs BigQuery)
│   ├── models/             # SQL models for staging and marts
│   │   ├── staging/        # Staging models (raw data → cleaned)
│   │   │   ├── schema.yml  # dbt schema configuration and tests
│   │   │   ├── stg_stations.sql          # Staging model for stations data
│   │   │   └── bigquery/   # BigQuery-specific staging models
│   │   │       └── external_raw_data.sql # External table definition for BigQuery
│   │   └── marts/          # Mart models (business-level aggregates)
│   │       ├── mart_city_comparison.sql      # City-level daily comparison metrics
│   │       ├── mart_city_hourly_trends.sql   # Hourly aggregation by city
│   │       ├── mart_station_ranking.sql      # Station ranking by utilization within city
│   │       ├── mart_station_utilization.sql  # Daily station-level metrics
│   │       └── mart_weekly_trends.sql        # Weekly aggregation by city
│   ├── profiles/           # DuckDB and BigQuery connection profiles
│   │   └── profiles.yml    # dbt profiles configuration
│   └── target/             # Compiled SQL and artifacts (generated, gitignored)
│
├── airflow/                # Orchestration using Apache Airflow
│   ├── dags/               # Airflow DAG definitions
│   │   ├── citybikes_pipeline.py          # Local pipeline DAG (DuckDB, every 30min)
│   │   └── citybikes_cloud_pipeline.py    # Cloud pipeline DAG (BigQuery/GCS, scheduled every 30 minutes)
│   ├── docker-compose.yml  # Docker Compose for local Airflow deployment
│   └── Dockerfile          # Custom Airflow image with dependencies
│
├── terraform/              # Cloud infrastructure as code (GCP)
│   ├── main.tf             # Main Terraform configuration
│   ├── variables.tf        # Input variable definitions
│   ├── outputs.tf          # Output values
│   ├── terraform.tfvars.example # Example variable values
│   ├── README.md           # Terraform module documentation
│   └── modules/            # Reusable Terraform modules
│       ├── gcs/            # Google Cloud Storage bucket module
│       │   ├── main.tf     # GCS bucket resource definition
│       │   ├── variables.tf # Module input variables
│       │   └── outputs.tf  # Module outputs (bucket name, URL)
│       ├── bigquery/       # BigQuery dataset and table module
│       │   ├── main.tf     # BigQuery dataset resource definition
│       │   ├── variables.tf # Module input variables
│       │   └── outputs.tf  # Module outputs (dataset ID, project)
│       ├── bigquery_external_table/ # External table module
│       │   ├── main.tf     # BigQuery external table resource definition
│       │   ├── variables.tf # Module input variables
│       │   └── outputs.tf  # Module outputs (table ID)
│       ├── iam/            # IAM permissions module
│       │   ├── main.tf     # IAM service account and role definitions
│       │   ├── variables.tf # Module input variables
│       │   └── outputs.tf  # Module outputs (service account email)
│       └── compute/        # Compute Engine VM module
│           ├── main.tf     # VM instance definition and startup script
│           ├── variables.tf # Module input variables
│           └── outputs.tf  # Module outputs (VM IP, name)
│
├── tests/                  # Unit and integration tests
│   ├── test_ingestion.py   # Tests for ingestion module
│   └── test_storage.py     # Tests for storage module
│
├── scripts/                # Utility scripts for development and operations
│   ├── run_ingestion.py    # CLI script to run the ingestion pipeline
│   ├── generate_sample_data.py # Generate sample data for testing
│   ├── historical_load.py  # Generate historical data with time patterns
│   ├── create_service_account_key.py # Create GCP service account key
│   └── generate_gcp_env.py # Generate environment variables for GCP
│
├── data/                   # Data directories (raw data excluded from git)
│   └── raw/                # Raw ingested data partitioned by date and city
│       └── date=YYYY-MM-DD/
│           └── city=Name/
│               └── stations_*.parquet  # Partitioned Parquet files
│
└── docs/                   # Project documentation
    ├── architecture.md     # System architecture and data flow
    ├── structure.md        # Repository structure (this file)
    ├── progress.md         # Phase completion status and tracking
    └── decisions.md        # Architectural decision records
```

## Detailed File Descriptions

### ingestion/
- `client.py` – HTTP client for CityBikes API v2 with retry logic (3 attempts, exponential backoff)
- `schemas.py` – Pydantic schemas for API response validation (NetworkListResponse, NetworkDetails, Station)
- `extractor.py` – Extracts and transforms station data from API responses, handles city filtering
- `loader.py` – Orchestrates extraction and storage process, manages city networks
- `utils.py` – Utility functions for logging, timestamp generation, and data formatting

### storage/
- `interface.py` – Abstract storage interface defining save() method for different backends
- `local.py` – Local filesystem storage implementation using Parquet format with date/city partitioning
- `gcs.py` – Google Cloud Storage implementation for uploading Parquet files to GCS bucket

### warehouse/
- `duckdb/` – Placeholder for DuckDB warehouse utilities (local development)
- `bigquery/` – Placeholder for BigQuery warehouse utilities (cloud production)

### dbt/
- `dbt_project.yml` – dbt project configuration including model paths, vars, and materialization settings
- `macros/create_external_raw_data.sql` – Macro for creating BigQuery external table over GCS Parquet files
- `macros/get_raw_data.sql` – Macro for raw data access, switches between DuckDB and BigQuery based on target
- `models/staging/schema.yml` – dbt schema configuration and data tests for staging models
- `models/staging/stg_stations.sql` – Staging model that cleans raw station data, derives slots field
- `models/staging/bigquery/external_raw_data.sql` – BigQuery-specific external table definition for raw data
- `models/marts/mart_city_comparison.sql` – City-level daily comparison metrics (total stations, avg utilization)
- `models/marts/mart_city_hourly_trends.sql` – Hourly aggregation by city for time-series analysis
- `models/marts/mart_station_ranking.sql` – Station ranking by utilization within each city
- `models/marts/mart_station_utilization.sql` – Daily station-level metrics (free bikes, empty slots, utilization rate)
- `models/marts/mart_weekly_trends.sql` – Weekly aggregation by city for longer-term trends
- `profiles/profiles.yml` – dbt profiles configuration for DuckDB (dev) and BigQuery (prod) targets

### airflow/
- `dags/citybikes_pipeline.py` – Airflow DAG for local pipeline (DuckDB) scheduled every 30 minutes
- `dags/citybikes_cloud_pipeline.py` – Airflow DAG for cloud pipeline (BigQuery/GCS) scheduled every 30 minutes
- `docker-compose.yml` – Docker Compose configuration for local Airflow deployment (PostgreSQL + LocalExecutor)
- `Dockerfile` – Custom Airflow image with Python dependencies and project code mounted

### terraform/
- `main.tf` – Main Terraform configuration defining GCS, BigQuery, IAM, and Compute modules
- `variables.tf` – Input variable definitions (project_id, region, bucket_name, dataset_id, etc.)
- `outputs.tf` – Output values (bucket name, dataset ID, service account email, VM IP)
- `terraform.tfvars.example` – Example variable values file (copy to terraform.tfvars)
- `README.md` – Terraform module documentation

#### terraform/modules/
- `gcs/main.tf`, `variables.tf`, `outputs.tf` – GCS bucket module with configurable storage class and location
- `bigquery/main.tf`, `variables.tf`, `outputs.tf` – BigQuery dataset module with description and labels
- `bigquery_external_table/main.tf`, `variables.tf`, `outputs.tf` – BigQuery external table module for raw Parquet data
- `iam/main.tf`, `variables.tf`, `outputs.tf` – IAM service account module with required permissions
- `compute/main.tf`, `variables.tf`, `outputs.tf` – Compute Engine VM module with startup script for pipeline orchestration

### tests/
- `test_ingestion.py` – Unit tests for ingestion module (client, schemas, extractor, loader)
- `test_storage.py` – Unit tests for storage module (interface, local, gcs)

### scripts/
- `run_ingestion.py` – CLI script to run ingestion pipeline with storage backend and network options
- `generate_sample_data.py` – Generate sample Parquet data for testing transformations
- `historical_load.py` – Generate historical data with realistic time patterns for time-series testing
- `create_service_account_key.py` – Create GCP service account key and update .env file
- `generate_gcp_env.py` – Generate environment variables from Terraform outputs and update .env

### data/
- `raw/` – Directory for raw ingested Parquet files partitioned by date and city (gitignored except .gitkeep)

### docs/
- `architecture.md` – System architecture and data flow diagrams
- `structure.md` – Repository structure (this file)
- `progress.md` – Phase completion status and tracking
- `decisions.md` – Architectural decision records

## Root-Level Files

* `pyproject.toml` – Python dependencies and project configuration
* `Makefile` – Common development tasks (testing, linting, ingestion, orchestration, cloud deployment)
* `CLAUDE.md` – Project instructions and phase order (strict development rules)
* `README.md` – Getting started guide and overview
* `.env.example` – Environment variables template (copy to .env)
* `.env` – Actual environment variables (gitignored, created from .env.example)
* `.gitignore` – Git ignore rules for Python, data, secrets, and build artifacts
* `.dockerignore` – Docker ignore rules for build context
* `citybikes-pipeline-sa-key.json` – Service account key for pipeline execution (gitignored, generated)
* `citybikes-terraform-sa-key.json` – Service account key for Terraform operations (gitignored, generated)

## Documentation

The `docs/` directory contains:
* `architecture.md` – System architecture and data flow diagrams
* `structure.md` – Repository structure (this file)
* `progress.md` – Phase completion status and tracking
* `decisions.md` – Architectural decision records (ADRs)

## Naming Conventions

* snake_case for files and directories
* clear, explicit names
* no abbreviations

## Module Responsibilities

### ingestion/
* API interaction with CityBikes public API
* schema validation using Pydantic
* data normalization and cleaning

### storage/
* abstract storage layer (interface)
* local filesystem (Parquet) and Google Cloud Storage implementations
* partition management (date/city)

### dbt/
* SQL transformations only (no business logic in ingestion)
* staging models clean raw data
* mart models create business-level aggregates (station utilization, city hourly trends, city comparison, station ranking, weekly trends)

### airflow/
* Orchestration using Apache Airflow
* Local development with Docker Compose (PostgreSQL + LocalExecutor)
* DAG definitions for scheduled pipeline execution (every 30 minutes)
* UI for monitoring and logs

### terraform/
* Infrastructure as code for Google Cloud Platform
* Modular design for GCS, BigQuery, IAM
* Supports both development and production environments

### scripts/
* command-line utilities for pipeline operations
* service account key generation
* environment setup

## Rule

Each module must be independently testable.
