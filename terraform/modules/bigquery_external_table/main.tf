# BigQuery external table for raw Parquet files in GCS

resource "google_bigquery_table" "external_table" {
  project    = var.project_id
  dataset_id = var.dataset_id
  table_id   = var.table_id

  description = var.description
  labels      = var.labels

  # External table configuration
  external_data_configuration {
    # Source format: Parquet
    source_format = "PARQUET"
    autodetect    = true

    # Source URIs (supports wildcards for partitioned data)
    source_uris = var.source_uris

    # Allow creation even if no files match initially
    ignore_unknown_values = true
    max_bad_records = 0

    # Hive partitioning options for city=CityName/date=YYYY-MM-DD structure
    hive_partitioning_options {
      mode                     = "AUTO"
      source_uri_prefix        = length(var.source_uris) > 0 ? replace(var.source_uris[0], "/*", "") : ""
      require_partition_filter = false
      fields                   = ["city", "date"]
    }

    # Parquet-specific options
    parquet_options {
      enable_list_inference    = true
      enum_as_string           = true
    }
  }

  # Do not manage table data with Terraform (external table only)
  deletion_protection = false
}