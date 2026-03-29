{{
config(
    materialized='table',
    schema='marts'
)
}}

select
    city,
    {{ dbt.date_trunc("week", "date") }} as week_start,
    avg(free_bikes) as avg_free_bikes,
    avg(free_bikes) / nullif(avg(free_bikes) + avg(empty_slots), 0) as avg_availability_rate,
    count(distinct station_id) as active_stations
from {{ ref('stg_stations') }}
group by 1, 2