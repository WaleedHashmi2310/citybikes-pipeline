from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = "/project"

with DAG(
    dag_id="citybikes_pipeline",
    description="Ingest CityBikes data, run dbt models and tests",
    schedule_interval="*/30 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["citybikes"],
) as dag:

    ingest = BashOperator(
        task_id="ingest_local",
        bash_command=f"cd {PROJECT_ROOT} && STORAGE_BACKEND=local python scripts/run_ingestion.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT_ROOT} && dbt run --project-dir dbt --profiles-dir dbt/profiles",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT_ROOT} && dbt test --project-dir dbt --profiles-dir dbt/profiles",
    )

    ingest >> dbt_run >> dbt_test