FROM apache/airflow:2.7.3-python3.11

# Switch to root to install system dependencies
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy project files
COPY --chown=airflow:airflow pyproject.toml /opt/airflow/project/
COPY --chown=airflow:airflow ingestion/ /opt/airflow/project/ingestion/
COPY --chown=airflow:airflow storage/ /opt/airflow/project/storage/
COPY --chown=airflow:airflow scripts/ /opt/airflow/project/scripts/
COPY --chown=airflow:airflow tests/ /opt/airflow/project/tests/
COPY --chown=airflow:airflow dbt/ /opt/airflow/project/dbt/
COPY --chown=airflow:airflow Makefile /opt/airflow/project/

# Install Python dependencies (install without editable mode to avoid pyproject.toml issues)
WORKDIR /opt/airflow/project
RUN pip install --upgrade pip && \
    pip install --no-cache-dir "requests>=2.31.0" "pydantic>=2.5.0" "tenacity>=8.2.0" "pandas>=2.0.0" "pyarrow>=14.0.0" \
    "google-cloud-storage>=2.10.0" "duckdb>=0.9.0" \
    "dbt-core==1.7.0" "dbt-duckdb==1.7.0" "dbt-bigquery==1.7.0"

# Set AIRFLOW_HOME
ENV AIRFLOW_HOME=/opt/airflow

# Switch back to project directory
WORKDIR /opt/airflow/project