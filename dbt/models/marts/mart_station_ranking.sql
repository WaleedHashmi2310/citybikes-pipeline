{{
config(
    materialized='table',
    schema='marts'
)
}}


select
    city,
    station_id,
    name,
    date,
    avg(free_bikes) as avg_free_bikes,
    avg(empty_slots) as avg_empty_slots,
    avg(free_bikes) / nullif(avg(free_bikes) + avg(empty_slots), 0) as avg_availability_rate,
    count(*) as reading_count,
    rank() over (partition by city, date order by avg(free_bikes) / nullif(avg(free_bikes) + avg(empty_slots), 0)) as utilization_rank
from {{ ref('stg_stations') }}
group by 1, 2, 3, 4