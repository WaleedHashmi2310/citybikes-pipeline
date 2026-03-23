# architecture.md

## Overview

This project builds a modular data pipeline using the CityBikes API.

## High-Level Flow

### Local Mode

API → Python Ingestion → Parquet (Local FS) → DuckDB → dbt → Marts

### Cloud Mode

API → Python Ingestion → GCS → BigQuery → dbt → Marts → Looker

## Components

### 1. Ingestion Layer

* Fetch city bike station data
* Normalize schema
* Append timestamp
* Write to storage

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

### 5. Orchestration

* Airflow DAG:

  * ingest → store → dbt run → dbt test

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
* timestamp
* ingestion_timestamp
* city

### Marts

* station utilization
* city-level aggregations

## Environments

* dev (local)
* prod (cloud)
