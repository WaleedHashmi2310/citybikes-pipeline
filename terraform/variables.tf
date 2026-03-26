# Root input variables for CityBikes pipeline infrastructure

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region for resources"
  type        = string
  default     = "europe-west1"
}

variable "bucket_name" {
  description = "Name of the GCS bucket for raw data (must be globally unique)"
  type        = string
}

variable "dataset_id" {
  description = "BigQuery dataset ID for data warehouse"
  type        = string
  default     = "citybikes"
}

variable "service_account_id" {
  description = "ID for the pipeline service account"
  type        = string
  default     = "citybikes-pipeline-sa"
}

variable "environment" {
  description = "Environment label (e.g., dev, prod)"
  type        = string
  default     = "dev"
}


