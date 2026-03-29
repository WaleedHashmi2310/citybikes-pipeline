FROM apache/airflow:2.9.1
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --upgrade pip && pip install \
    requests>=2.31.0 \
    pydantic>=2.5.0 \
    tenacity>=8.2.0 \
    pandas>=2.0.0 \
    pyarrow>=14.0.0 \
    google-cloud-storage>=2.10.0 \
    duckdb==1.5.1 \
    dbt-core==1.11.7 \
    dbt-duckdb==1.10.1 \
    dbt-bigquery==1.11.1