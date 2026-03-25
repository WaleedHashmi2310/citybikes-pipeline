# CityBikes Data Pipeline

End-to-end data pipeline for CityBikes API.

## Overview

This project implements a robust data pipeline that ingests, stores, transforms, and visualizes data from the CityBikes API. It supports both local development (DuckDB) and cloud deployment (BigQuery).

## Architecture

- **Ingestion**: Python modules for API interaction with retry logic and schema validation
- **Storage**: Abstract storage layer supporting local Parquet files and Google Cloud Storage
- **Warehouse**: DuckDB for local development, BigQuery for cloud production
- **Transformations**: dbt models for data cleaning and aggregation
- **Orchestration**: Apache Airflow DAGs for pipeline scheduling
- **Infrastructure**: Terraform for cloud resource provisioning
- **CI/CD**: GitHub Actions for automated testing and deployment

## Project Structure

See [docs/structure.md](docs/structure.md) for details.

## Getting Started

### Prerequisites

- Python 3.12+
- Git

### Installation

1. Clone the repository
2. Create virtual environment: `python -m venv .venv`
3. Activate virtual environment: `source .venv/bin/activate`
4. Install dependencies: `pip install -e .`

**Alternative using Makefile:**
```bash
make setup  # Creates virtual environment and installs dependencies
```

### Environment Variables

1. Copy the environment template: `cp .env.example .env` (or use `make env-setup`)
2. Edit `.env` with your configuration:
   - For local development with DuckDB: Set `DBT_DUCKDB_PATH` (default: `citybikes.duckdb`)
   - For cloud deployment with BigQuery/GCS: Set all BigQuery and Google Cloud variables
3. Load environment variables into your shell:
   ```bash
   export $(grep -v '^#' .env | xargs)
   ```
   Or use a tool like `direnv` or `dotenv`.

See [.env.example](.env.example) for detailed variable descriptions.

### Quick Start with Makefile

The project includes a comprehensive Makefile for common tasks:

```bash
# Show all available commands
make help

# Set up environment and install dependencies
make setup

# Copy environment template and configure
make env-setup
# Edit .env file with your configuration

# Run full local pipeline: ingestion → dbt → data tests
make pipeline

# Individual steps
make ingest-local           # Extract data and store as Parquet files
make dbt-run               # Run dbt transformations
make dbt-test              # Run data quality tests
make test                  # Run unit tests
```

### Simplified Workflow

For streamlined deployment, use these high-level targets:

```bash
# Local development: Set up environment and start Airflow with Docker
make local

# Cloud deployment: Provision GCP resources and start Airflow VM
make cloud

# Run pipeline directly in cloud mode (after cloud setup)
make cloud-pipeline

# Destroy all GCP resources
make cloud-destroy
```

### Manual Usage

You can also run the ingestion script directly:

```bash
# Basic ingestion with default German cities
python scripts/run_ingestion.py --storage local

# Custom network list
python scripts/run_ingestion.py --networks "callabike-frankfurt,stadtrad-hamburg-db"

# GCS storage (requires GCS_BUCKET_NAME in .env)
python scripts/run_ingestion.py --storage gcs --bucket your-bucket-name

# See all options
python scripts/run_ingestion.py --help
```

### Orchestration with Airflow (Docker)

The pipeline is orchestrated using Apache Airflow running in Docker:

```bash
# Build and start Airflow with Docker
make docker-airflow

# View logs
make docker-logs

# Stop services
make docker-down
```

Access Airflow UI at http://localhost:8080 (admin/admin). The DAG `citybikes_pipeline` runs daily and executes:
1. Data ingestion from CityBikes API
2. dbt transformations
3. Data quality tests

See [docs/RUNNING_AIRFLOW.md](docs/RUNNING_AIRFLOW.md) for detailed instructions.

### Cloud Orchestration on GCP

For production deployment on Google Cloud Platform, several cost-effective options are available. For the simplest deployment experience, use `make cloud` which automates Option 1 (Compute Engine VM):

#### Option 1: Compute Engine VM (Cheapest)
Deploy the Docker Compose setup to a small Compute Engine instance:
- **Cost**: ~$15/month for e2-micro instance
- **Setup**: Terraform module for VM with Docker and docker-compose
- **Management**: Manual updates, automatic startup on boot

#### Option 2: Cloud Run Jobs + Cloud Scheduler
Convert pipeline tasks to individual Cloud Run Jobs triggered by Cloud Scheduler:
- **Cost**: Pay-per-use, scales to zero
- **Setup**: Containerize each task (ingestion, dbt run, dbt test)
- **Management**: Serverless, no infrastructure to manage

#### Option 3: GKE Autopilot
Run Airflow on managed Kubernetes:
- **Cost**: ~$50-100/month depending on usage
- **Setup**: Deploy Airflow Helm chart with our DAGs
- **Management**: Google-managed Kubernetes nodes

#### Common Prerequisites for All Options:

```bash
# Generate environment variables from Terraform outputs
python scripts/generate_gcp_env.py --format bash > gcp.env

# Create service account key for GCP authentication
python scripts/create_service_account_key.py

# Set environment variables for cloud execution
export STORAGE_BACKEND=gcs
export DBT_TARGET=prod
source gcp.env
```

#### Deployment Steps for Option 1: Compute Engine VM

> **Tip**: The `make cloud` command automates all steps below.

1. **Configure Terraform**: Edit `terraform/terraform.tfvars` and set:
   ```hcl
   enable_vm          = true
   vm_source_repo_url = "https://github.com/your-username/citybikes-pipeline.git"  # Your fork
   ```

2. **Apply infrastructure**: Run `make terraform-apply` to create the VM along with other resources.

3. **Wait for startup**: The VM startup script installs Docker, clones the repository, and starts Airflow (~5 minutes). Monitor progress via Google Cloud Console.

4. **Access Airflow UI**: After startup, navigate to `http://$(terraform output -raw airflow_vm_external_ip):8080` (credentials: admin/admin).

5. **Verify pipeline**: The DAG `citybikes_pipeline` runs hourly. Check the Airflow UI for successful runs.

**Notes**:
- The VM uses the service account created by Terraform (no key file needed).
- Port 8080 is open to the internet; restrict firewall rules for production.
- Data persists in the VM's boot disk; consider separate persistent disk for PostgreSQL.
- To update the pipeline, push changes to your repository and restart the VM or run `git pull` inside the VM.

For Options 2 and 3, refer to separate deployment guides (to be implemented).

### Cloud Infrastructure with Terraform

Cloud resources (GCS bucket, BigQuery dataset, IAM service account) are managed via Terraform. The `make cloud` command automates the entire provisioning process:

```bash
# Initialize Terraform
make terraform-init

# Generate execution plan (requires terraform.tfvars)
make terraform-plan

# Apply infrastructure changes (requires GCP credentials)
make terraform-apply

# Show output values (bucket name, dataset ID, service account email)
make terraform-output

# Format and validate configuration
make terraform-fmt
make terraform-validate
```

**Setup steps:**

1. **Create `terraform.tfvars`**: Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and fill in your GCP project details.
2. **Configure credentials**: Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable or use `gcloud auth application-default login`.
3. **Apply infrastructure**: Run `make terraform-apply` to create resources.
4. **Update environment variables**: After Terraform outputs values, update your `.env` file with:
   - `GCS_BUCKET_NAME` (from `bucket_name` output)
   - `DBT_BIGQUERY_PROJECT` (your project ID)
   - `DBT_BIGQUERY_DATASET` (from `dataset_id` output)
   - Service account key (manually create and download)

See [terraform/README.md](terraform/README.md) for detailed Terraform module documentation.

### Development

Follow the phased implementation approach outlined in [CLAUDE.md](CLAUDE.md).

## License

MIT