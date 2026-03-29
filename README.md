# CityBikes Data Pipeline

End-to-end data pipeline for CityBikes API.

## Overview

This project implements a robust data pipeline that ingests, stores, transforms, and visualizes data from the CityBikes API. It supports both local development (DuckDB) and cloud deployment (BigQuery).

## Architecture

- **Ingestion**: Python modules for API interaction with retry logic and schema validation
- **Storage**: Abstract storage layer supporting local Parquet files and Google Cloud Storage
- **Warehouse**: DuckDB for local development, BigQuery for cloud production
- **Transformations**: dbt models for data cleaning and aggregation
- **Execution**: Manual pipeline execution via Makefile targets or scheduled via Apache Airflow (local)
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
make historical-load       # Generate historical data with time patterns
```

### Simplified Workflow

For streamlined deployment, use these high-level targets:

```bash
# Local development: Set up environment and run full pipeline
make local

# Cloud deployment: Provision GCP resources and configure environment
make cloud

# Run pipeline directly in cloud mode (after cloud setup)
make cloud-pipeline

# Destroy all GCP resources
make cloud-destroy
```

### Local Orchestration with Apache Airflow

For scheduled local orchestration, you can run the pipeline using Apache Airflow in Docker containers:

```bash
# Start Airflow (PostgreSQL + LocalExecutor)
make airflow-up

# Stop Airflow
make airflow-down

# Reset Airflow (stop and wipe volumes)
make airflow-reset
```

Access the Airflow UI at http://localhost:8080 (admin/admin) to monitor DAG runs and logs.

The Airflow setup mounts the project directory as a volume, so code changes are reflected without rebuilding the image. Raw data is stored in `data/raw` and the DuckDB database in `citybikes.duckdb`.

The DAG `citybikes_pipeline` runs every 30 minutes, executing ingestion (local storage), dbt run, and dbt test tasks.

### Historical Data Generation

Generate realistic historical station data for testing time-series analytics:

```bash
# Generate data for last 7 days with 30-minute intervals
make historical-load

# Custom parameters via environment variables
make historical-load HISTORICAL_DAYS_BACK=3 HISTORICAL_INTERVAL_MINUTES=60

# Direct script usage
python scripts/historical_load.py --days-back 3 --interval-minutes 120 --networks "callabike-berlin,stadtrad-hamburg-db" --storage local
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


### Cloud Deployment Options

For production deployment on Google Cloud Platform, several cost-effective options are available. The `make cloud` command automates infrastructure provisioning (GCS bucket, BigQuery dataset, IAM service account) and environment configuration, but does not deploy an orchestrator. Choose one of these deployment patterns:

#### Option 1: Compute Engine VM (Manual Setup)
Deploy the pipeline to a small Compute Engine instance and run it manually or via cron:
- **Cost**: ~$15/month for e2-micro instance
- **Setup**: Manual VM creation, install dependencies, clone repository
- **Management**: Manual updates, automatic startup on boot
- **Execution**: Run `make cloud-pipeline` manually or schedule via cron

#### Option 2: Cloud Run Jobs + Cloud Scheduler
Convert pipeline tasks to individual Cloud Run Jobs triggered by Cloud Scheduler:
- **Cost**: Pay-per-use, scales to zero
- **Setup**: Containerize each task (ingestion, dbt run, dbt test)
- **Management**: Serverless, no infrastructure to manage

#### Option 3: GKE Autopilot (Kubernetes)
Run pipeline on managed Kubernetes using Kubernetes Jobs or an orchestrator like Argo Workflows:
- **Cost**: ~$50-100/month depending on usage
- **Setup**: Deploy pipeline containers to GKE Autopilot
- **Management**: Google-managed Kubernetes nodes
- **Execution**: Schedule via Kubernetes CronJobs or workflow orchestrator

#### Common Prerequisites for All Options:

```bash
# Generate environment variables from Terraform outputs and update .env file
python scripts/generate_gcp_env.py --format dotenv --update-env

# Create service account key for GCP authentication (updates .env automatically)
python scripts/create_service_account_key.py

# Set environment variables for cloud execution
export STORAGE_BACKEND=gcs
export DBT_TARGET=prod
source .env  # or use export $(grep -v '^#' .env | xargs)
```

#### Manual VM Setup (Option 1):
If you choose Option 1, follow these general steps:

1. **Create a Compute Engine VM** with desired specifications (e2-micro recommended)
2. **Install dependencies**: Docker, docker-compose, Python, git
3. **Clone repository** and copy pipeline code to VM
4. **Copy service account key** and `.env` file to VM
5. **Run pipeline manually**: `make cloud-pipeline` or schedule via cron

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
4. **Configure environment**: Use the automation scripts to update `.env` with Terraform outputs and create service account key:
   ```bash
   # Update .env with GCS bucket, BigQuery dataset, and project
   python scripts/generate_gcp_env.py --format dotenv --update-env
   # Create service account key and update .env with key file path
   python scripts/create_service_account_key.py
   ```

See [terraform/README.md](terraform/README.md) for detailed Terraform module documentation.

### Development

Follow the phased implementation approach outlined in [CLAUDE.md](CLAUDE.md).

## License

MIT