# Input variables for BigQuery external table module

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "dataset_id" {
  description = "BigQuery dataset ID where the external table will be created"
  type        = string
}

variable "table_id" {
  description = "BigQuery external table ID"
  type        = string
  default     = "external_raw_data"
}

variable "source_uris" {
  description = "List of Google Cloud Storage URIs for Parquet files (supports wildcards)"
  type        = list(string)
  default     = ["*.parquet"]  # Should be overridden
}

variable "description" {
  description = "Description of the external table"
  type        = string
  default     = "External table pointing to raw Parquet files in GCS"
}

variable "labels" {
  description = "Resource labels"
  type        = map(string)
  default     = {}
}