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
│   ├── models/             # SQL models for staging and marts
│   │   ├── staging/        # Staging models (raw data → cleaned)
│   │   └── marts/          # Mart models (business-level aggregates)
│   ├── macros/             # Reusable SQL macros
│   ├── profiles/           # DuckDB and BigQuery connection profiles
│   └── dbt_project.yml     # dbt project configuration
│
├── airflow/                # Orchestration using Apache Airflow
│   ├── dags/               # Airflow DAG definitions
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
│       ├── bigquery/       # BigQuery dataset and table module
│       ├── bigquery_external_table/ # External table module
│       └── iam/            # IAM permissions module
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
│               └── stations_*.parquet
│
├── docs/                   # Project documentation
│   ├── architecture.md     # System architecture and data flow
│   ├── structure.md        # Repository structure (this file)
│   ├── progress.md         # Phase completion status
│   └── decisions.md        # Architectural decision records
│
└── .github/workflows/      # CI/CD pipelines (GitHub Actions)
```

## Root-Level Files

* `pyproject.toml` – Python dependencies and project configuration
* `Makefile` – Common development tasks (testing, linting, ingestion)
* `CLAUDE.md` – Project instructions and phase order (strict development rules)
* `README.md` – Getting started guide and overview
* `.env.example` – Environment variables template (copy to .env)
* `.gitignore` – Git ignore rules for Python, data, secrets, and build artifacts
* `.dockerignore` – Docker ignore rules for build context

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
