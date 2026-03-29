{{
config(
    materialized='table',
    schema='marts'
)
}}

with daily_station_data as (
    select
        station_id,
        name,
        city,
        date,
        -- Use provided slots if available, otherwise infer from free_bikes + empty_slots
        coalesce(slots, free_bikes + empty_slots) as total_slots,
        free_bikes,
        empty_slots,
        slots,
        station_timestamp,
        ingestion_timestamp
    from {{ ref('stg_stations') }}
),

aggregated as (
    select
        station_id,
        name,
        city,
        date,
        count(*) as readings_count,
        avg(free_bikes) as avg_free_bikes,
        avg(empty_slots) as avg_empty_slots,
        avg(total_slots) as avg_total_slots,
        -- Utilization rate: free bikes / total slots
        avg(1.0 * free_bikes / nullif(total_slots, 0)) as avg_utilization_rate,
        max(station_timestamp) as latest_station_timestamp,
        max(ingestion_timestamp) as latest_ingestion_timestamp
    from daily_station_data
    group by 1, 2, 3, 4
)

select * from aggregated