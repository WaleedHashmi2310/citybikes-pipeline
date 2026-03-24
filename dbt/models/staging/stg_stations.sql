{{
config(
    materialized='view',
    schema='staging'
)
}}

-- Read raw Parquet files from the data/raw directory
-- Uses DuckDB's read_parquet function with glob pattern

with raw_data as (
    select
        station_id,
        name,
        latitude,
        longitude,
        free_bikes,
        empty_slots,
        timestamp as station_timestamp,
        ingestion_timestamp,
        city,
        date
    from read_parquet('{{ var("raw_data_path", "data/raw") }}/**/*.parquet')
)

select
    station_id,
    name,
    latitude,
    longitude,
    free_bikes,
    empty_slots,
    -- Parse timestamps
    cast(station_timestamp as timestamp) as station_timestamp,
    cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
    city,
    date
from raw_data