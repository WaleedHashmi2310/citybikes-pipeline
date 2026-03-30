# 🚲 CityBikes ELT Pipeline – Compare Bike Sharing Across German Cities

**An end-to-end data pipeline that extracts, loads, and transforms real‑time bike‑sharing data from 12 major German cities. Run locally with DuckDB or deploy to Google Cloud with BigQuery. Perfect for learning modern data engineering or monitoring urban mobility trends.**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![dbt](https://img.shields.io/badge/dbt-✓-FF694B.svg)](https://docs.getdbt.com/)
[![Apache Airflow](https://img.shields.io/badge/Airflow-✓-007A88.svg)](https://airflow.apache.org/)
[![Terraform](https://img.shields.io/badge/Terraform-✓-7B42BC.svg)](https://terraform.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 What’s This About?

City‑bike systems in Germany are booming, but **how do their utilization patterns differ?** Do Hamburg’s stations fill up faster than Berlin’s? Is Munich more active on weekends than Frankfurt? This pipeline answers those questions by:

1. **Ingesting** live station data every 30 minutes from the [CityBikes API](https://api.citybik.es/v2/) for 12 major German networks.
2. **Storing** the data in a partitioned, append‑only format (local Parquet or Google Cloud Storage).
3. **Transforming** raw records into clean, analyzable tables using **dbt**.
4. **Producing** ready‑to‑use **data marts** that compare cities, rank stations, and track hourly/weekly trends.
5. **Orchestrating** the entire flow with **Apache Airflow**—locally via Docker or in the cloud on a GCP Compute Engine VM.

### 🎯 What You’ll Get Out of It

* **City‑level comparison**: Daily total stations, average utilization, free‑bike ratios across Berlin, Hamburg, Munich, Cologne, Frankfurt, Stuttgart, Leipzig, Dresden, Düsseldorf, Mainz.
* **Hourly trends**: See how usage peaks during rush hours in each city.
* **Station ranking**: Identify the most‑ and least‑used stations in each network.
* **Weekly patterns**: Compare weekday vs. weekend activity.
* **A fully‑functional ELT pipeline** that you can extend, customize, or deploy as a production monitoring tool.

---

## 🛠️ Prerequisites

**For local mode (DuckDB)**
*   **Python 3.12+** – the project uses modern Python features.
*   **Git** – to clone the repository.
*   **Docker & Docker Compose** – to run Airflow locally (optional; you can also run the pipeline manually).

**For cloud mode (BigQuery / GCS)**
*   Everything above, plus:
*   **Google Cloud Platform account** – with a project where you can create resources (free tier eligible).
*   **gcloud CLI** – authenticated with `gcloud auth application-default login` or a service‑account key.
*   **Terraform ≥1.5** – to provision the cloud infrastructure.

**All dependencies are managed inside a Python virtual environment; you never need to install packages globally.**

---

## 🏗️ Architecture at a Glance

The pipeline is built as a **dual‑mode ELT system**: the same code runs either locally (with DuckDB and local Parquet files) or in the cloud (with BigQuery and Google Cloud Storage). Orchestration is handled by Apache Airflow, scheduled every 30 minutes.

![Pipeline Architecture](docs/architecture-diagram.svg)

### 🔄 Data Flow

1.  **Extract** – Python client calls the CityBikes API, validates responses with Pydantic schemas, and adds ingestion timestamps.
2.  **Load** – Abstract storage layer writes partitioned Parquet files to either the local filesystem (`data/raw/date=.../city=...`) or a GCS bucket.
3.  **Transform** – dbt models turn raw data into **staging** (cleaned, typed) and **mart** tables (business‑level aggregates).
4.  **Orchestrate** – Airflow DAGs glue the steps together and run on schedule.
5.  **Visualize** (optional) – Connect Looker Studio to the BigQuery marts for live dashboards.

### 📦 Key Technologies

| Layer           | Local Stack              | Cloud Stack               |
|-----------------|--------------------------|---------------------------|
| **Storage**     | Parquet on disk          | Google Cloud Storage      |
| **Warehouse**   | DuckDB                   | BigQuery                  |
| **Orchestrator**| Airflow (Docker Compose) | Airflow (GCP Compute VM)  |
| **Infra as Code**| –                        | Terraform                 |

---

## 🚀 Let’s Get Started

Choose your path: **local mode** for quick experimentation, or **cloud mode** for a production‑like deployment. Both follow the same three‑step pattern:

1.  **Dry run** – execute the pipeline once manually.
2.  **Historical load** – generate realistic time‑series data for testing.
3.  **Orchestration** – schedule the pipeline to run automatically every 30 minutes.

---

## 🖥️ Local Mode (DuckDB + Parquet)

Run the entire pipeline on your laptop with **zero cloud dependencies**. Data is stored as Parquet files and transformed in a local DuckDB database.

### 📦 Step 0: Clone & Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/citybikes-pipeline.git
cd citybikes-pipeline

# 2. Set up Python environment and install dependencies
make setup

# 3. Copy environment template (no changes needed for local DuckDB)
make env-setup
```

That’s it! The `.env` file already contains the default `DBT_DUCKDB_PATH=citybikes.duckdb`. The virtual environment (`.venv`) is ready.

### 🧪 Step 1: Dry Run – Execute the Pipeline Once

Run the full ELT cycle **once** to verify everything works:

```bash
make pipeline
```

What happens under the hood:
1.  `make ingest-local` – fetches current station data from all 12 German networks and writes partitioned Parquet files to `data/raw/date=.../city=...`.
2.  `make dbt-run` – runs dbt models that create staging tables (cleaned raw data) and five data marts in `citybikes.duckdb`.
3.  `make dbt-test` – executes data quality tests (e.g., non‑negative free_bikes, valid timestamps).

**Check the results:**
```bash
# Inspect the raw Parquet files
ls -la data/raw/*/*/*.parquet

# Query the DuckDB database (requires duckdb CLI)
duckdb citybikes.duckdb \
  "SELECT city, COUNT(*) AS stations FROM stg_stations GROUP BY city;"
```

### 📅 Step 2: Historical Load – Generate Time‑Series Test Data

The CityBikes API only returns current snapshots. To test time‑series aggregations, generate synthetic historical data that mimics real usage patterns:

```bash
# Generate 7 days of data with 30‑minute intervals (default)
make historical-load

# Customize: 3 days, hourly intervals, only Berlin & Hamburg
make historical-load HISTORICAL_DAYS_BACK=3 HISTORICAL_INTERVAL_MINUTES=60 NETWORKS="callabike-berlin,stadtrad-hamburg-db"
```

The script creates realistic timestamps, simulates daily/weekly cycles, and writes Parquet files with the same partition structure as live ingestion. All generated records include a `_generated = true` flag so you can distinguish them from real API data.

### ⏰ Step 3: Orchestration – Schedule with Airflow (Optional)

To run the pipeline automatically every 30 minutes, start the local Airflow stack (Docker Compose):

```bash
# Start Airflow (PostgreSQL + LocalExecutor)
make airflow-up
```

Wait a minute for containers to initialize, then open **http://localhost:8080** (login: `admin` / `admin`). You’ll see the DAG `citybikes_pipeline` already enabled and scheduled.

**What’s inside the Airflow setup:**
*   The project directory is mounted as a volume – code changes are reflected immediately.
*   Raw data lands in `data/raw` (same as manual runs).
*   DuckDB database is at `citybikes.duckdb` (same as manual runs).
*   DAG runs every 30 minutes, executing `ingest_local` → `dbt_run` → `dbt_test`.

**Useful commands:**
```bash
# Stop Airflow (keeps volumes)
make airflow-down

# Stop and wipe all Airflow data (reset)
make airflow-reset
```

### 🧹 Clean Up Local Environment

```bash
# Remove virtual environment, DuckDB file, raw data, and dbt artifacts
make clean
```

---

## ☁️ Cloud Mode (BigQuery + Google Cloud Storage)

Deploy the pipeline to Google Cloud for a production‑ready setup. Data flows from the API → GCS bucket → BigQuery external table → dbt transformations → BigQuery marts.

### ⚙️ Step 0: Prerequisites & Authentication

1.  **Google Cloud Project** – create one in the [Cloud Console](https://console.cloud.google.com).
2.  **Enable APIs** – BigQuery, Cloud Storage, IAM, Compute Engine (if using VM orchestration).
3.  **Install & authenticate gcloud CLI**:
    ```bash
    gcloud auth application-default login
    # OR use a service account key (see Terraform step below)
    ```
4.  **Install Terraform** (≥1.5) – [instructions](https://developer.hashicorp.com/terraform/install).

### 🏗️ Step 1: Provision Cloud Infrastructure with Terraform

The repository includes a Terraform module that creates a GCS bucket, BigQuery dataset, IAM service account, and (optionally) a Compute Engine VM for Airflow.

```bash
# 1. Navigate to terraform directory and copy the variables template
cd terraform
cp terraform.tfvars.example terraform.tfvars

# 2. Edit terraform.tfvars – fill in your GCP project ID and region
#    (leave other values as defaults unless you need to customize)

# 3. Initialize Terraform and apply the configuration
make terraform-init    # from project root
make terraform-plan
make terraform-apply   # confirms creation of bucket, dataset, service account, VM
```

After `terraform apply`, note the outputs: bucket name, dataset ID, service account email, and VM IP (if you opted for the VM module).

### 🔑 Step 2: Configure Environment for Cloud Execution

Two helper scripts automate the setup of your `.env` file:

```bash
# Update .env with GCS bucket name, BigQuery dataset, project ID, etc.
python scripts/generate_gcp_env.py --format dotenv --update-env

# Create a service‑account key file and update DBT_BIGQUERY_KEYFILE in .env
python scripts/create_service_account_key.py
```

Now your `.env` contains all the required cloud variables (`GCS_BUCKET_NAME`, `DBT_BIGQUERY_PROJECT`, `DBT_BIGQUERY_DATASET`, `DBT_BIGQUERY_KEYFILE`, …).

### 🧪 Step 3: Dry Run – Execute the Cloud Pipeline Once

With infrastructure ready, run the full cloud pipeline manually:

```bash
make cloud-pipeline
```

What happens:
1.  `STORAGE_BACKEND=gcs` – ingestion writes Parquet files directly to your GCS bucket.
2.  `DBT_TARGET=prod` – dbt uses the BigQuery profile and materializes models in BigQuery.
3.  The same five data marts are built in BigQuery, ready for analysis.

**Verify in BigQuery:**
*   Go to [BigQuery Console](https://console.cloud.google.com/bigquery).
*   You’ll see a dataset named `citybikes` (or whatever you configured) with tables `stg_stations`, `mart_station_utilization`, `mart_city_hourly_trends`, etc.

### 📅 Step 4: Historical Load – Generate Cloud Test Data

Generate historical Parquet files and upload them to GCS:

```bash
# Generate 7 days of data and store directly in GCS
make historical-load STORAGE_BACKEND=gcs GCS_BUCKET_NAME=$(grep GCS_BUCKET_NAME .env | cut -d= -f2)

# Customize days, interval, networks
make historical-load HISTORICAL_DAYS_BACK=3 HISTORICAL_INTERVAL_MINUTES=120 NETWORKS="callabike-berlin,stadtrad-hamburg-db" STORAGE_BACKEND=gcs
```

The script uses the same GCS storage backend as live ingestion, so the generated files land in the same bucket partition structure.


### ⏰ Step 5: Orchestration – Airflow on a GCP Compute Engine VM

If you used the Terraform `compute` module, a VM with Docker and the repository cloned is waiting for you. However, Airflow containers are not automatically started. Follow these steps to deploy Airflow and schedule the pipeline:

**Prepare the VM:**
1.  Note the VM external IP from Terraform outputs.
2.  Copy your local `.env` file to the VM (required for environment variables):
    ```bash
    gcloud compute scp .env citybikes-airflow-vm:/opt/citybikes-pipeline/.env
    ```
3.  SSH into the VM and start Airflow:
    ```bash
    gcloud compute ssh citybikes-airflow-vm
    cd /opt/citybikes-pipeline
    make airflow-up
    ```
    Wait 2–3 minutes for the containers to initialize.

**Access the cloud Airflow UI:**
1.  Open `http://<VM_IP>:8080` (login: `admin` / `admin`).
2.  The DAG `citybikes_cloud_pipeline` is already scheduled and will run every 30 minutes.

**What’s inside the VM setup:**
*   Docker and docker‑compose installed via startup script.
*   Repository cloned into `/opt/citybikes-pipeline`.
*   Firewall rules allow inbound traffic on ports 8080 (Airflow UI) and 22 (SSH).
*   The attached service account provides permissions to access GCS and BigQuery (no key file needed).

**Manual triggering from your local machine (optional):**
```bash
# Run the cloud pipeline remotely via SSH
gcloud compute ssh citybikes-airflow-vm --command "cd /opt/citybikes-pipeline && make cloud-pipeline"
```
### 🗑️ Step 6: Destroy Cloud Resources (When Done)

To avoid ongoing costs, tear down all created resources:

```bash
make cloud-destroy   # runs terraform destroy -auto-approve
```

**Warning:** This deletes the GCS bucket (and all data inside), BigQuery dataset, service account, and VM. Only run when you no longer need the pipeline.

---

## 🛠️ Makefile Cheat Sheet

The project’s `Makefile` is your Swiss‑army knife. Run `make help` to see all targets.

| Target | Description |
|--------|-------------|
| `make setup` | Create virtual environment and install all dependencies. |
| `make pipeline` | Local dry‑run: ingest → dbt run → dbt test. |
| `make ingest-local` | Fetch live data and store as local Parquet. |
| `make ingest-networks NETWORKS="..."` | Ingest only specific networks. |
| `make dbt-run` | Run dbt transformations (uses current target). |
| `make dbt-test` | Run dbt data quality tests. |
| `make historical-load` | Generate historical test data (local). |
| `make airflow-up` | Start local Airflow stack (Docker). |
| `make cloud` | Provision GCP infrastructure + configure `.env`. |
| `make cloud-pipeline` | Run full pipeline in cloud mode. |
| `make cloud-destroy` | Destroy all GCP resources. |
| `make test` | Run unit tests (pytest). |
| `make lint` | Lint Python code (flake8). |
| `make format` | Format code with black/isort. |
| `make clean` | Remove virtual env, data, DuckDB file, dbt artifacts. |

---

## 📚 Documentation

*   **[docs/architecture.md](docs/architecture.md)** – detailed architecture and data flow.
*   **[docs/structure.md](docs/structure.md)** – complete repository layout.
*   **[docs/progress.md](docs/progress.md)** – project phase completion status.
*   **[docs/decisions.md](docs/decisions.md)** – architectural decision records (ADRs).
*   **[CLAUDE.md](CLAUDE.md)** – development rules and phase order.

---

## 📄 License

MIT License

---

## 🙏 Acknowledgements

*   Data provided by the [CityBikes API](https://api.citybik.es/v2/).
*   Built with [Python](https://python.org), [dbt](https://docs.getdbt.com/), [Apache Airflow](https://airflow.apache.org/), [DuckDB](https://duckdb.org/), [BigQuery](https://cloud.google.com/bigquery), [Terraform](https://terraform.io).
*   Inspired by the need to compare urban bike‑sharing systems across Germany.

