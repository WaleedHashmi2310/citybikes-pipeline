{% if target.type == 'bigquery' %}
-- External table already created manually via DDL
-- This model is disabled to avoid conflict with existing external table
{{
config(
    materialized='table',
    enabled=false
)
}}
select
    null as station_id,
    null as name,
    null as latitude,
    null as longitude,
    null as free_bikes,
    null as empty_slots,
    null as timestamp,
    null as ingestion_timestamp,
    null as city,
    null as date
where false

{% else %}
-- This model is only for BigQuery
-- For other adapters, create an empty CTE to avoid errors
{{
config(
    materialized='ephemeral',
    enabled=false
)
}}
select
    null as station_id,
    null as name,
    null as latitude,
    null as longitude,
    null as free_bikes,
    null as empty_slots,
    null as timestamp,
    null as ingestion_timestamp,
    null as city,
    null as date
where false
{% endif %}