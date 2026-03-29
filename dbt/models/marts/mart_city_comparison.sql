{{
config(
    materialized='table',
    schema='marts'
)
}}

select
    city,
    date,
    count(distinct station_id) as total_stations,
    avg(free_bikes) as avg_free_bikes,
    avg(empty_slots) as avg_empty_slots,
    avg(free_bikes) / nullif(avg(free_bikes) + avg(empty_slots), 0) as avg_availability_rate,
    sum(case when free_bikes = 0 then 1 else 0 end) / count(*) as pct_empty_readings,
    sum(case when empty_slots = 0 then 1 else 0 end) / count(*) as pct_full_readings
from {{ ref('stg_stations') }}
group by 1, 2