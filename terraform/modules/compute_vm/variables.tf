# Input variables for Compute Engine VM module

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region for resources"
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "Google Cloud zone for VM instance"
  type        = string
  default     = "europe-west1-b"
}

variable "vm_name" {
  description = "Name of the Compute Engine instance"
  type        = string
  default     = "citybikes-airflow-vm"
}

variable "machine_type" {
  description = "Machine type for the VM instance"
  type        = string
  default     = "e2-micro"  # 2 vCPU, 1 GB memory
}

variable "disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 20
}

variable "service_account_email" {
  description = "Service account email for VM instance"
  type        = string
}

variable "bucket_name" {
  description = "GCS bucket name for raw data"
  type        = string
}

variable "dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
}

variable "bigquery_location" {
  description = "BigQuery location (region)"
  type        = string
  default     = "europe-west1"
}

variable "source_repo_url" {
  description = "Git repository URL to clone for the pipeline"
  type        = string
  default     = "https://github.com/username/citybikes-pipeline.git"
}

variable "branch_name" {
  description = "Git branch to checkout"
  type        = string
  default     = "main"
}

variable "labels" {
  description = "Labels to apply to the VM instance"
  type        = map(string)
  default     = {}
}

variable "enable_public_ip" {
  description = "Whether to assign a public IP address to the VM"
  type        = bool
  default     = true
}

variable "airflow_ui_port" {
  description = "Port for Airflow UI (will be opened in firewall)"
  type        = number
  default     = 8080
}