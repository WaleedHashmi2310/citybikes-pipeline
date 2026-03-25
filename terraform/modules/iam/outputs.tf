# Output values for IAM module

output "service_account_email" {
  description = "Email address of the created service account"
  value       = google_service_account.service_account.email
}