# Compute Engine VM for Airflow orchestration

# Startup script to install Docker, clone repo, and start Airflow
data "template_file" "startup_script" {
  template = file("${path.module}/startup_script.sh.tpl")

  vars = {
    project_id           = var.project_id
    service_account_email = var.service_account_email
    bucket_name          = var.bucket_name
    dataset_id           = var.dataset_id
    bigquery_location    = var.bigquery_location
    source_repo_url      = var.source_repo_url
    branch_name          = var.branch_name
  }
}

# Compute Engine instance
resource "google_compute_instance" "airflow_vm" {
  name         = var.vm_name
  machine_type = var.machine_type
  zone         = var.zone
  project      = var.project_id

  tags = ["airflow", "http-server"]

  boot_disk {
    initialize_params {
      image = "debian-11-bullseye-v20240312"
      size  = var.disk_size_gb
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"

    # Assign public IP if enabled
    dynamic "access_config" {
      for_each = var.enable_public_ip ? [1] : []
      content {
        # Ephemeral IP
      }
    }
  }

  # Use the pipeline service account
  service_account {
    email  = var.service_account_email
    scopes = ["cloud-platform"]
  }

  # Startup script to install Docker and start Airflow
  metadata_startup_script = data.template_file.startup_script.rendered

  labels = var.labels
}

# Firewall rule to allow Airflow UI access
resource "google_compute_firewall" "airflow_ui" {
  name    = "${var.vm_name}-airflow-ui"
  network = "default"
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = [var.airflow_ui_port]
  }

  # Allow from any source (restrict in production)
  source_ranges = ["0.0.0.0/0"]

  target_tags = ["airflow"]
}

