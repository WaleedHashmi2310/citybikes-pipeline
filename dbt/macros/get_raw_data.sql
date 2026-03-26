{% macro get_raw_data() %}
  {# Returns SQL expression to read raw data based on adapter (partitioned by date then city) #}

  {% if target.type == 'duckdb' %}
    -- DuckDB: read local Parquet files
    read_parquet('{{ var("raw_data_path", "data/raw") }}/**/*.parquet')

  {% elif target.type == 'bigquery' %}
    -- BigQuery: read Parquet files from GCS bucket
    {% set bucket_name = var("gcs_bucket_name", "citybikes-elt-de-bucket") %}
    -- Using BigQuery's external table query syntax for partitioned Parquet files
    `{{ target.database }}.{{ env_var('DBT_BIGQUERY_DATASET') }}.external_raw_data`

  {% else %}
    {{ exceptions.raise_compiler_error("Adapter " ~ target.type ~ " not supported for raw data reading") }}
  {% endif %}
{% endmacro %}