resource "google_compute_instance" "airflow_vm" {
  name         = var.vm_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 30
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.airflow_ip.address
    }
  }

  service_account {
    email  = var.service_account_email
    scopes = ["cloud-platform"]
  }

  metadata = {
    startup-script = <<-EOF
        #!/bin/bash
        set -e

        # Install Docker
        apt-get update
        apt-get install -y ca-certificates curl gnupg git make
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

        # Add current user to docker group
        CURRENT_USER=$(getent passwd 1000 | cut -d: -f1)
        usermod -aG docker $CURRENT_USER

        # Clone repo
        git clone https://github.com/WaleedHashmi2310/citybikes-pipeline.git /opt/citybikes-pipeline
        chmod -R 777 /opt/citybikes-pipeline
    EOF
  }

  tags = ["airflow-vm"]

  labels = var.labels
}

resource "google_compute_address" "airflow_ip" {
  name   = "${var.vm_name}-ip"
  region = var.region
}

resource "google_compute_firewall" "airflow_ui" {
  name    = "${var.vm_name}-allow-airflow"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8080", "22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["airflow-vm"]
}
