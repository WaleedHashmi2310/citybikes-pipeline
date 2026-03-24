# structure.md

## Repository Structure

```
project_root/
│
├── ingestion/              # API client, schemas, extraction logic
│   ├── client.py
│   ├── schemas.py
│   ├── extractor.py
│   ├── loader.py
│   └── utils.py
│
├── storage/                # Storage abstraction (local Parquet / GCS)
│   ├── interface.py
│   ├── local.py
│   └── gcs.py
│
├── warehouse/              # Warehouse-specific configs (future use)
│   ├── duckdb/
│   └── bigquery/
│
├── dbt/                    # dbt transformations
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── profiles/           # DuckDB and BigQuery profiles
│   └── dbt_project.yml
│
├── airflow/                # Airflow orchestration (Docker only)
│   ├── dags/
│   │   └── citybikes_pipeline.py
│   └── plugins/
│
├── terraform/              # Cloud infrastructure as code
│
├── tests/                  # Unit and integration tests
│   ├── test_ingestion.py
│   ├── test_storage.py
│   └── conftest.py
│
├── scripts/                # Utility scripts
│   ├── run_ingestion.py
│   └── generate_sample_data.py
│
├── data/                   # Data directories (raw data excluded from git)
│   └── raw/
│
├── .github/workflows/      # CI/CD pipelines
│
└── docs/                   # Project documentation
```

## Root-Level Files

* `pyproject.toml` – Python dependencies and project config
* `Makefile` – Common development tasks
* `CLAUDE.md` – Project instructions and phase order
* `README.md` – Getting started guide
* `docker-compose.yml` – Airflow services definition
* `Dockerfile` – Custom Airflow image
* `.env.example` – Environment variables template
* `.gitignore` – Git ignore rules

## Documentation

The `docs/` directory contains:
* `architecture.md` – System architecture and data flow
* `structure.md` – Repository structure (this file)
* `progress.md` – Phase completion status
* `decisions.md` – Architectural decision records
* `RUNNING_AIRFLOW.md` – Airflow Docker setup and usage

## Naming Conventions

* snake_case for files and directories
* clear, explicit names
* no abbreviations

## Module Responsibilities

### ingestion/
* API interaction
* schema validation
* data normalization

### storage/
* abstract storage layer
* local vs cloud interchangeable

### dbt/
* transformations only

### airflow/
* orchestration only (Docker-based)

### scripts/
* command-line utilities
* sample data generation

## Rule

Each module must be independently testable.
