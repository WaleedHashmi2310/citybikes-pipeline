# Google Cloud Storage bucket for CityBikes raw data
resource "google_storage_bucket" "bucket" {
  name          = var.bucket_name
  location      = var.location
  project       = var.project_id
  storage_class = var.storage_class

  # Enable uniform bucket-level access (recommended)
  uniform_bucket_level_access = true
  force_destroy               = var.force_destroy

  # Versioning configuration
  versioning {
    enabled = var.versioning_enabled
  }

  # Lifecycle rules (optional)
  dynamic "lifecycle_rule" {
    for_each = var.lifecycle_rules
    content {
      action {
        type = lifecycle_rule.value.action_type
      }
      condition {
        age = lifecycle_rule.value.condition_age
      }
    }
  }

  # Labels for resource identification
  labels = var.labels
}