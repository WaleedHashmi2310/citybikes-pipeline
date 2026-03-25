"""
CityBikes Pipeline DAG

Orchestrates the data pipeline:
1. Ingest data from CityBikes API
2. Run dbt transformations
3. Run dbt data tests

Environment variables required for cloud execution:
- STORAGE_BACKEND: 'gcs' for cloud, 'local' for local
- DBT_TARGET: 'prod' for BigQuery, 'dev' for DuckDB
- GCS_BUCKET_NAME: GCS bucket name (for gcs storage)
- DBT_BIGQUERY_PROJECT: GCP project ID (for BigQuery)
- DBT_BIGQUERY_DATASET: BigQuery dataset ID
- GOOGLE_APPLICATION_CREDENTIALS: path to service account key (for gcs storage)
- CITYBIKES_NETWORKS: comma-separated network IDs (optional)
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "start_date": datetime(2026, 3, 24),
}

# Project root directory - configurable via environment variable
# Default: two levels up from DAG file (assuming project_root/airflow/dags structure)
PROJECT_ROOT = os.environ.get('CITYBIKES_PROJECT_ROOT',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Define the DAG
dag = DAG(
    "citybikes_pipeline",
    default_args=default_args,
    description="End-to-end CityBikes data pipeline",
    schedule=timedelta(hours=1),  # Run every hour
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=False,
    concurrency=1,
    tags=["citybikes", "data-pipeline"],
)

# Task 1: Ingest data from CityBikes API
ingest = BashOperator(
    task_id="ingest",
    bash_command="python scripts/run_ingestion.py",
    cwd=PROJECT_ROOT,
    dag=dag,
)

# Task 2: Run dbt transformations
dbt_run = BashOperator(
    task_id="dbt_run",
    bash_command="dbt run --project-dir dbt --profiles-dir dbt/profiles",
    cwd=PROJECT_ROOT,
    dag=dag,
)

# Task 3: Run dbt data tests
dbt_test = BashOperator(
    task_id="dbt_test",
    bash_command="dbt test --project-dir dbt --profiles-dir dbt/profiles",
    cwd=PROJECT_ROOT,
    dag=dag,
)

# Set task dependencies
ingest >> dbt_run >> dbt_test