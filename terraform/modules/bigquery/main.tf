# BigQuery dataset for CityBikes data warehouse
resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  project                     = var.project_id
  location                    = var.location
  friendly_name               = var.friendly_name
  description                 = var.description
  default_table_expiration_ms = var.default_table_expiration_ms

  # Labels for resource identification
  labels = var.labels
  delete_contents_on_destroy = var.delete_contents_on_destroy
}