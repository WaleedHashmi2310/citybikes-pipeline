{{
config(
    materialized='table',
    schema='marts'
)
}}

with station_utilization as (
    select
        city,
        date,
        station_id,
        free_bikes,
        empty_slots,
        free_bikes + empty_slots as total_slots
    from {{ ref('stg_stations') }}
),

city_aggregates as (
    select
        city,
        date,
        count(distinct station_id) as station_count,
        sum(free_bikes) as total_free_bikes,
        sum(empty_slots) as total_empty_slots,
        sum(total_slots) as total_slots,
        avg(1.0 * free_bikes / nullif(total_slots, 0)) as avg_city_utilization_rate,
        -- Percentage of stations with at least one bike available
        avg(case when free_bikes > 0 then 1.0 else 0.0 end) as pct_stations_with_bikes
    from station_utilization
    group by 1, 2
)

select * from city_aggregates