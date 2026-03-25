# Input variables for GCS bucket module

variable "bucket_name" {
  description = "Name of the GCS bucket (must be globally unique)"
  type        = string
}

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "location" {
  description = "Bucket location (region or multi-region)"
  type        = string
  default     = "EU"
}

variable "storage_class" {
  description = "Storage class for the bucket"
  type        = string
  default     = "STANDARD"
}

variable "versioning_enabled" {
  description = "Enable versioning for bucket objects"
  type        = bool
  default     = false
}

variable "lifecycle_rules" {
  description = "List of lifecycle rule configurations"
  type = list(object({
    action_type   = string
    condition_age = number
  }))
  default = []
}

variable "force_destroy" {
  description = "Whether to force destroy bucket even if it contains objects (use with caution)"
  type        = bool
  default     = false
}

variable "labels" {
  description = "Resource labels for identification"
  type        = map(string)
  default     = {}
}