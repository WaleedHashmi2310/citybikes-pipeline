# Output values for GCS bucket module

output "bucket_name" {
  description = "Name of the created GCS bucket"
  value       = google_storage_bucket.bucket.name
}

output "self_link" {
  description = "URI of the created GCS bucket"
  value       = google_storage_bucket.bucket.self_link
}

output "url" {
  description = "Base URL of the bucket"
  value       = "gs://${google_storage_bucket.bucket.name}"
}