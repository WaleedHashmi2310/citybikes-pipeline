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

### Environment Variables

1. Copy the environment template: `cp .env.example .env`
2. Edit `.env` with your configuration:
   - For local development with DuckDB: Set `DBT_DUCKDB_PATH` (default: `citybikes.duckdb`)
   - For cloud deployment with BigQuery/GCS: Set all BigQuery and Google Cloud variables
3. Load environment variables into your shell:
   ```bash
   export $(grep -v '^#' .env | xargs)
   ```
   Or use a tool like `direnv` or `dotenv`.

See [.env.example](.env.example) for detailed variable descriptions.

### Development

Follow the phased implementation approach outlined in [CLAUDE.md](CLAUDE.md).

## License

MIT