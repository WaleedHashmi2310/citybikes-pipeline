# decisions.md

## dbt over PySpark

* Data volume is small
* SQL transformations are sufficient
* Easier local/cloud parity
* Lower complexity

## DuckDB for Local

* Zero setup
* Works natively with Parquet
* dbt adapter available

## BigQuery for Cloud

* Serverless
* Native integration with GCS
* Works with Looker

## Manual Execution via Makefile

* Simplified orchestration using Makefile targets
* No dedicated orchestrator dependency
* Easy local development with `make pipeline`
* Cloud execution with `make cloud-pipeline`
* Environment-based configuration for local/cloud modes

## Airflow for Local Orchestration

* Provides scheduled execution (every 30 minutes) without manual intervention
* Docker Compose setup for easy local deployment
* UI for monitoring DAG runs and logs
* Retry logic and dependency management built-in
* Maintains manual Makefile targets for development and cloud execution
* LocalExecutor with PostgreSQL backend for simplicity

## Append-Only Strategy

* Preserves history
* Enables time-based analytics
* Simplifies ingestion logic

## Static City List

* Ensures deterministic pipeline
* Avoids API variability

## Terraform for Infra

* Reproducibility
* Version control for infra

## Minimal Monitoring

* Pipeline logs
* dbt tests
* No heavy observability tools

## Historical Data Generation

* Generate realistic test data with time-based patterns
* Supports local and cloud storage backends
* Configurable date ranges and intervals

## CI/CD (Basic)

* Lint + pytest
* dbt build (DuckDB)
