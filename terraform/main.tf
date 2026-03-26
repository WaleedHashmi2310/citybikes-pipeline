# CityBikes Pipeline - Cloud Infrastructure
# Terraform root configuration

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Optional: remote backend configuration (uncomment and adjust as needed)
  # backend "gcs" {
  #   bucket = "tf-state-bucket-name"
  #   prefix = "citybikes-pipeline"
  # }
}

# Google Cloud provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Local variables for resource labeling
locals {
  common_labels = {
    environment = var.environment
    project     = "citybikes-pipeline"
    managed_by  = "terraform"
  }
  zone = "${var.region}-b"
}

# GCS bucket for raw Parquet data
module "gcs_bucket" {
  source = "./modules/gcs"

  bucket_name        = var.bucket_name
  project_id         = var.project_id
  location           = var.region
  storage_class      = "STANDARD"
  versioning_enabled = false
  force_destroy      = var.environment == "dev" ? true : false
  labels             = merge(local.common_labels, { component = "storage" })
}

# BigQuery dataset for data warehouse
module "bigquery_dataset" {
  source = "./modules/bigquery"

  dataset_id    = var.dataset_id
  project_id    = var.project_id
  location      = var.region
  friendly_name = "CityBikes Data Warehouse"
  description   = "CityBikes station data warehouse for analytics"
  labels        = merge(local.common_labels, { component = "warehouse" })
}

# IAM service account and permissions for pipeline
module "iam_service_account" {
  source = "./modules/iam"

  service_account_id = var.service_account_id
  project_id         = var.project_id
  display_name       = "CityBikes Pipeline Service Account"
  description        = "Service account for CityBikes data pipeline operations"
}

# # BigQuery external table for raw Parquet files in GCS
# # Commented out: dbt will create external table as needed during pipeline execution
# # This avoids Terraform dependency on GCS files existing at provisioning time
# module "bigquery_external_table" {
#   source = "./modules/bigquery_external_table"
#
#   project_id = var.project_id
#   dataset_id = module.bigquery_dataset.dataset_id
#   table_id   = "external_raw_data"
#   source_uris = [
#     "${module.gcs_bucket.url}/raw/*"
#   ]
#   description = "External table for CityBikes raw station data (partitioned by date and city)"
#   labels      = merge(local.common_labels, { component = "external-table" })
# }

