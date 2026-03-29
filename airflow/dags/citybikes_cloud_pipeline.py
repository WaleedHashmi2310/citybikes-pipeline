from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = "/project"

with DAG(
    dag_id="citybikes_cloud_pipeline",
    description="Ingest CityBikes data to GCS, run dbt models on BigQuery",
    schedule_interval="*/30 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["citybikes", "cloud"],
) as dag:

    ingest = BashOperator(
        task_id="ingest_gcs",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"set -a && source .env && set +a && "
            f"STORAGE_BACKEND=gcs python scripts/run_ingestion.py"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"set -a && source .env && set +a && "
            f"dbt run --project-dir dbt --profiles-dir dbt/profiles"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"set -a && source .env && set +a && "
            f"dbt test --project-dir dbt --profiles-dir dbt/profiles"
        ),
    )

    ingest >> dbt_run >> dbt_test