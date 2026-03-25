# Input variables for BigQuery dataset module

variable "dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
}

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "location" {
  description = "Dataset location (region or multi-region)"
  type        = string
  default     = "EU"
}

variable "friendly_name" {
  description = "Human-readable name for the dataset"
  type        = string
  default     = "CityBikes Data Warehouse"
}

variable "description" {
  description = "Dataset description"
  type        = string
  default     = "CityBikes station data warehouse for analytics"
}

variable "default_table_expiration_ms" {
  description = "Default expiration time for tables (in milliseconds)"
  type        = number
  default     = null  # No expiration by default
}

variable "delete_contents_on_destroy" {
  description = "Whether to delete dataset contents on destroy (use with caution)"
  type        = bool
  default     = false
}

variable "labels" {
  description = "Resource labels for identification"
  type        = map(string)
  default     = {}
}