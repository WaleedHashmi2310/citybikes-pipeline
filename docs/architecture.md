# architecture.md

## Overview

This project builds a modular data pipeline using the CityBikes API.

## High-Level Flow

### Local Mode

API → Python Ingestion → Parquet (Local FS) → DuckDB → dbt → Marts

Orchestration: manual (`make pipeline`) or automated (Airflow DAG scheduled every 30 minutes)

### Cloud Mode

API → Python Ingestion → GCS → BigQuery → dbt → Marts → Looker

## Components

### 1. Ingestion Layer

* Fetch city bike station data
* Normalize schema
* Append timestamp
* Write to storage
* Historical data generation with realistic time patterns (scripts/historical_load.py)

### 2. Storage Layer

* Local: Parquet files partitioned by date/city
* Cloud: GCS buckets

### 3. Warehouse Layer

* DuckDB (local)
* BigQuery (cloud)

### 4. Transformation Layer

* dbt:

  * staging
  * marts

### 5. Orchestration Layer

* **Manual execution**: Makefile targets for local development and testing:

  * `make pipeline` (local) / `make cloud-pipeline` (cloud)
  * Sequence: ingest → store → dbt run → dbt test

* **Automated orchestration**: Apache Airflow for scheduled local pipeline runs:

  * Docker Compose setup with PostgreSQL backend and LocalExecutor
  * DAG scheduled every 30 minutes (`citybikes_pipeline`)
  * Tasks: ingest_local (STORAGE_BACKEND=local) → dbt_run → dbt_test
  * Make targets: `airflow-up`, `airflow-down`, `airflow-reset`

### 6. Visualization

* Looker Studio connected to BigQuery marts

## Data Model

### Raw

* station_id
* name
* latitude
* longitude
* free_bikes
* empty_slots
* slots – total station capacity (derived from extra.slots or free_bikes + empty_slots)
* extra – JSON string containing operational metadata (renting, returning, etc.)
* timestamp
* ingestion_timestamp
* city

### Marts

* station utilization – daily station-level metrics
* city hourly trends – hourly aggregation by city
* city comparison – city-level daily comparison metrics
* station ranking – station ranking by utilization within city
* weekly trends – weekly aggregation by city

## Environments

* dev (local)
* prod (cloud)
