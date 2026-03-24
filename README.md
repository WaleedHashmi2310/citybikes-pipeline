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

### Development

Follow the phased implementation approach outlined in [CLAUDE.md](CLAUDE.md).

## License

MIT