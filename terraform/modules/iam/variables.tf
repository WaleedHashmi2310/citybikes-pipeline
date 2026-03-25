# Input variables for IAM module

variable "service_account_id" {
  description = "ID for the service account (must be unique within project)"
  type        = string
}

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "display_name" {
  description = "Human-readable display name for the service account"
  type        = string
  default     = "CityBikes Pipeline Service Account"
}

variable "description" {
  description = "Description of the service account"
  type        = string
  default     = "Service account for CityBikes data pipeline operations"
}