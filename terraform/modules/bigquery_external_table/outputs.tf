# Outputs for BigQuery external table module

output "table_id" {
  description = "ID of the created external table"
  value       = google_bigquery_table.external_table.table_id
}

output "fully_qualified_name" {
  description = "Fully qualified name of the external table (project.dataset.table)"
  value       = "${google_bigquery_table.external_table.project}.${google_bigquery_table.external_table.dataset_id}.${google_bigquery_table.external_table.table_id}"
}