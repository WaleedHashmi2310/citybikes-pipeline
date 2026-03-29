{{
config(
    materialized='view',
    schema='staging',
    pre_hook=[
        "{{ create_external_raw_data() }}"
    ]
)
}}

-- Read raw Parquet files from the data/raw directory
-- Uses DuckDB's read_parquet function with glob pattern for local development
-- Uses BigQuery external table for cloud production

{% if target.type == 'duckdb' %}
    -- DuckDB: read local Parquet files
    with raw_data as (
        select
            station_id,
            name,
            latitude,
            longitude,
            free_bikes,
            empty_slots,
            slots,
            extra,
            timestamp as station_timestamp,
            ingestion_timestamp,
            city,
            date
        from read_parquet('{{ var("raw_data_path", "/data/raw") }}/**/*.parquet')
    )

    select
        station_id,
        name,
        latitude,
        longitude,
        free_bikes,
        empty_slots,
        slots,
        extra,
        -- DuckDB: cast directly (Parquet types should match)
        cast(station_timestamp as timestamp) as station_timestamp,
        cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
        city,
        date
    from raw_data

{% elif target.type == 'bigquery' %}
    -- BigQuery: read from external table over GCS Parquet files
    with raw_data as (
        select
            station_id,
            name,
            latitude,
            longitude,
            free_bikes,
            empty_slots,
            slots,
            extra,
            timestamp as station_timestamp,
            ingestion_timestamp,
            city,
            date
        from {{ get_raw_data() }}
    )

    select
        station_id,
        name,
        latitude,
        longitude,
        free_bikes,
        empty_slots,
        slots,
        extra,
        -- BigQuery: timestamp is ISO string, ingestion_timestamp is nanoseconds
        TIMESTAMP(station_timestamp) as station_timestamp,
        TIMESTAMP_SECONDS(CAST(ingestion_timestamp / 1000000000 AS INT64)) as ingestion_timestamp,
        city,
        date
    from raw_data

{% else %}
    {{ exceptions.raise_compiler_error("Adapter " ~ target.type ~ " not supported") }}
{% endif %}