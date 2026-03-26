{% macro create_external_raw_data() %}
  {# Creates external table for raw Parquet files in GCS if it doesn't exist (partitioned by date then city) #}

  {% if target.type == 'bigquery' %}
    {% set bucket_name = var("gcs_bucket_name", "citybikes-elt-de-bucket") %}
    {% set dataset = env_var('DBT_BIGQUERY_DATASET') %}
    {% set project = target.database %}

    {% set sql %}
      CREATE OR REPLACE EXTERNAL TABLE `{{ project }}.{{ dataset }}.external_raw_data`
      WITH PARTITION COLUMNS (
        date DATE,
        city STRING
      )
      OPTIONS (
        format = 'PARQUET',
        uris = ['gs://{{ bucket_name }}/raw/*'],
        hive_partition_uri_prefix = 'gs://{{ bucket_name }}/raw',
        require_hive_partition_filter = false
      );
    {% endset %}

    {{ log("Creating external table for GCS Parquet files: " ~ sql, info=true) }}
    {{ return(sql) }}

  {% else %}
    {{ log("Skipping external table creation for non-BigQuery target: " ~ target.type, info=true) }}
    {{ return("") }}
  {% endif %}
{% endmacro %}