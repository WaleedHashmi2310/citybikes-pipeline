# For GCP deployment, use standard Airflow image
# For local development, can use apache/airflow (see docker-compose.yml)
ARG BASE_IMAGE=apache/airflow:2.7.3-python3.11
FROM ${BASE_IMAGE}

# Username for the runtime user (airflow for apache/airflow)
ARG USERNAME=airflow

# Switch to root to install system dependencies
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Switch back to runtime user (airflow for apache/airflow)
USER ${USERNAME}

# Copy project files
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml /opt/airflow/project/
COPY --chown=${USERNAME}:${USERNAME} ingestion/ /opt/airflow/project/ingestion/
COPY --chown=${USERNAME}:${USERNAME} storage/ /opt/airflow/project/storage/
COPY --chown=${USERNAME}:${USERNAME} scripts/ /opt/airflow/project/scripts/
COPY --chown=${USERNAME}:${USERNAME} tests/ /opt/airflow/project/tests/
COPY --chown=${USERNAME}:${USERNAME} dbt/ /opt/airflow/project/dbt/
COPY --chown=${USERNAME}:${USERNAME} Makefile /opt/airflow/project/

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