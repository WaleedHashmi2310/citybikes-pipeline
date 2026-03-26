# progress.md

## Phase 0: Project Setup

* [x] Git repo initialized
* [x] GitHub repo created + pushed
* [x] Python 3.12 venv created
* [x] pyproject.toml created
* [x] Dependencies installed
* [x] README.md created

## Phase 1: Ingestion

* [x] API client implemented
* [x] Pydantic schema defined
* [x] Data extraction working
* [x] Retry logic implemented
* [x] Unit tests passing

## Phase 2: Storage

* [x] Local storage (Parquet)
* [x] GCS storage
* [x] Interface abstraction
* [x] Tests passing

## Phase 3: dbt

* [x] DuckDB profile
* [x] BigQuery profile
* [x] Staging models
* [x] Mart models
* [x] Tests

## Phase 4: Orchestration (removed)

* [x] Airflow/Kestra orchestration removed from project

## Phase 5: Cloud

* [x] Terraform infra
* [x] GCS bucket
* [x] BigQuery dataset
* [x] IAM roles
* [x] Cloud ingestion test (Frankfurt stations → GCS)
* [x] dbt transformations on BigQuery (europe-west1)
* [x] Data tests (9/10 passing, 1 type mismatch accepted_values)

## Phase 6: CI/CD

* [ ] GitHub Actions
* [ ] pytest runs
* [ ] dbt build runs

## Phase 7: Dashboard

* [ ] Looker dashboard created
