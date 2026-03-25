# Output values for CityBikes pipeline infrastructure

output "project_id" {
  description = "Google Cloud project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud region for resources"
  value       = var.region
}

output "bucket_name" {
  description = "Name of the created GCS bucket"
  value       = module.gcs_bucket.bucket_name
}

output "bucket_url" {
  description = "GS URL of the bucket"
  value       = module.gcs_bucket.url
}

output "dataset_id" {
  description = "ID of the created BigQuery dataset"
  value       = module.bigquery_dataset.dataset_id
}

output "service_account_email" {
  description = "Email address of the pipeline service account"
  value       = module.iam_service_account.service_account_email
}

output "airflow_vm_external_ip" {
  description = "External IP address of the Airflow VM (if created)"
  value       = try(module.compute_vm[0].external_ip, null)
}

output "airflow_vm_internal_ip" {
  description = "Internal IP address of the Airflow VM (if created)"
  value       = try(module.compute_vm[0].internal_ip, null)
}

output "airflow_vm_name" {
  description = "Name of the Airflow VM (if created)"
  value       = try(module.compute_vm[0].vm_name, null)
}