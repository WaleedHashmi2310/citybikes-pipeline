#!/bin/bash
# Startup script for CityBikes Airflow VM
# This script installs Docker, clones the repository, and starts Airflow with Docker Compose.

set -e  # Exit on error
set -x  # Print commands

# Update package list and install prerequisites
apt-get update
apt-get install -y \
    curl \
    git \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker using convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install docker-compose (standalone)
curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add current user to docker group (if not root)
if [ "$USER" != "root" ]; then
    usermod -aG docker $USER
fi

# Clone the repository
git clone ${source_repo_url} /opt/citybikes-pipeline
cd /opt/citybikes-pipeline
git checkout ${branch_name}

# Create environment variables file for cloud execution
cat > .env << EOF
# Cloud deployment configuration
STORAGE_BACKEND=gcs
DBT_TARGET=prod

# GCP infrastructure (from Terraform)
GCS_BUCKET_NAME=${bucket_name}
DBT_BIGQUERY_PROJECT=${project_id}
DBT_BIGQUERY_DATASET=${dataset_id}
DBT_BIGQUERY_LOCATION=${bigquery_location}

# Service account authentication (VM uses default credentials)
# GOOGLE_APPLICATION_CREDENTIALS is not needed when using VM service account
EOF

# Build and start Airflow with Docker Compose
make docker-airflow

# Wait a moment for services to start
sleep 30

# Print connection information
echo "================================================"
echo "Airflow deployment completed!"
echo "Airflow UI will be available at:"
echo "  http://$(curl -s ifconfig.me):8080"
echo "Credentials: admin / admin"
echo "================================================"