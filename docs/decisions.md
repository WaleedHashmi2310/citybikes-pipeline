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

## Airflow (Astro)

* Industry standard orchestration
* DAG-based control
* Easy Docker integration

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

* Airflow logs
* dbt tests
* No heavy observability tools

## CI/CD (Basic)

* Lint + pytest
* dbt build (DuckDB)
