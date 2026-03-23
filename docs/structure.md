# structure.md

## Repository Structure

```
project_root/
│
├── ingestion/
│   ├── client.py
│   ├── schemas.py
│   ├── extractor.py
│   ├── loader.py
│   └── utils.py
│
├── storage/
│   ├── local.py
│   ├── gcs.py
│   └── interface.py
│
├── warehouse/
│   ├── duckdb/
│   └── bigquery/
│
├── dbt/
│   ├── models/
│   ├── profiles/
│   └── dbt_project.yml
│
├── airflow/
│   ├── dags/
│   └── plugins/
│
├── terraform/
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_storage.py
│
├── data/
│   └── raw/
│
├── .github/workflows/
│
└── docs/
```

## Naming Conventions

* snake_case for files
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

* orchestration only

## Rule

Each module must be independently testable.
