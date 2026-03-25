# Output values for BigQuery dataset module

output "dataset_id" {
  description = "ID of the created BigQuery dataset"
  value       = google_bigquery_dataset.dataset.dataset_id
}

output "self_link" {
  description = "URI of the created dataset"
  value       = google_bigquery_dataset.dataset.self_link
}