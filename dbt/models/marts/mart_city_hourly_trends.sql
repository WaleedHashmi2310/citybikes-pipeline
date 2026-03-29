{{
config(
    materialized='table',
    schema='marts'
)
}}

select
    city,
    date,
    extract(hour from station_timestamp) as hour_of_day,
    extract(dayofweek from date) as day_of_week,
    avg(free_bikes) as avg_free_bikes,
    avg(empty_slots) as avg_empty_slots,
    sum(free_bikes) as total_free_bikes,
    count(distinct station_id) as active_stations
from {{ ref('stg_stations') }}
where station_timestamp is not null
group by 1, 2, 3, 4