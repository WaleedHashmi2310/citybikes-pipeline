variable "vm_name" {
  description = "Name of the Compute Engine VM"
  type        = string
  default     = "citybikes-airflow-vm"
}

variable "machine_type" {
  description = "GCP machine type"
  type        = string
  default     = "e2-medium"
}

variable "zone" {
  description = "GCP zone for the VM"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "service_account_email" {
  description = "Service account email to attach to the VM"
  type        = string
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}