# Running Airflow Orchestration (Docker Only)

This document explains how to run the CityBikes pipeline orchestration using Apache Airflow in Docker.

## Pipeline Polling Interval

The pipeline runs **daily** (every 24 hours) as configured in `airflow/dags/citybikes_pipeline.py`:
```python
schedule=timedelta(days=1),  # Run daily
```

You can adjust this by modifying the `schedule` parameter in the DAG file:
- `timedelta(hours=1)` for hourly runs
- `timedelta(minutes=30)` for every 30 minutes
- `timedelta(days=7)` for weekly runs
- `"0 0 * * *"` for cron expression (daily at midnight)

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available for Docker

### Quick Start with Makefile

```bash
# Build and start Airflow with Docker
make docker-airflow

# View logs
make docker-logs

# Stop services
make docker-down
```

### Manual Docker Commands

1. **Build the custom Airflow image**:
   ```bash
   docker-compose build
   ```

2. **Initialize Airflow database**:
   ```bash
   docker-compose up airflow-init
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Check running services**:
   ```bash
   docker-compose ps
   ```

### Access

- **Airflow UI**: http://localhost:8080
  - Username: `admin`
  - Password: `admin`
- **PostgreSQL**: localhost:5432
  - Database: `airflow`
  - User: `airflow`
  - Password: `airflow`

### Stopping

```bash
# Stop and remove containers
docker-compose down

# Stop containers but keep volumes
docker-compose stop
```

### Data Persistence

- **PostgreSQL data**: Persisted in Docker volume `postgres-db-volume`
- **Project code**: Mounted from host directory (`./` → `/opt/airflow/project`)
- **Airflow logs**: Stored in `./airflow/logs/` on host
- **DAG files**: Mounted from `./airflow/dags/` on host

## DAG Tasks

The pipeline consists of three sequential tasks that run automatically based on the schedule:

1. **ingest**: Extract data from CityBikes API → store as partitioned Parquet files
2. **dbt_run**: Transform raw data through staging → marts (DuckDB)
3. **dbt_test**: Validate data quality with dbt tests

## Docker Architecture

- **citybikes-airflow:latest**: Custom Airflow image with project dependencies
- **postgres:13**: PostgreSQL database for Airflow metadata
- **airflow-webserver**: Airflow UI (port 8080)
- **airflow-scheduler**: Airflow scheduler for DAG execution
- **airflow-init**: One-time initialization service

## Using Makefile Targets

The Makefile provides convenient shortcuts for Docker operations:

| Target | Description |
|--------|-------------|
| `make docker-build` | Build Docker image |
| `make docker-up` | Start services in background |
| `make docker-down` | Stop and remove services |
| `make docker-logs` | View service logs |
| `make docker-airflow` | Build and start (full setup) |

## Testing the Pipeline

### Manual DAG Trigger

1. Access Airflow UI at http://localhost:8080
2. Find "citybikes_pipeline" DAG
3. Click the play button (▶) next to the DAG name
4. Select "Trigger DAG" to run immediately

### Viewing Execution Results

- **DAG Runs**: Click on DAG name → "Graph" or "Grid" view
- **Task Logs**: Click on task instance → "Log" button
- **Historical Runs**: DAG → "Runs" tab

## Troubleshooting

### Common Issues

**Build failures**:
```bash
# Check Docker build logs
docker-compose build --no-cache
```

**Permission errors** (Linux):
```bash
echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=$(id -g)" > .env
docker-compose build
```

**Port conflicts**:
- Change port in `docker-compose.yml` (webserver ports mapping)
- Or stop other services using port 8080

**Container can't access host files**:
- Ensure Docker has permission to mount host directories
- Check Docker Desktop file sharing settings (macOS/Windows)

**DAG not appearing**:
- Check `airflow/dags/citybikes_pipeline.py` exists
- View scheduler logs: `docker-compose logs airflow-scheduler`

### Checking Service Health

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs airflow-scheduler
docker-compose logs airflow-webserver

# Check container status
docker-compose ps

# Restart services
docker-compose restart
```

## Production Considerations

For production deployment:

1. **Set secure passwords** in `docker-compose.yml`
2. **Enable HTTPS** for Airflow UI
3. **Configure external PostgreSQL** for better performance
4. **Set up backup** for PostgreSQL volume
5. **Configure monitoring** and alerting
6. **Use Kubernetes** instead of Docker Compose for scaling

## Next Steps

- Set up authentication for Airflow UI
- Configure email alerts for task failures
- Add monitoring and alerting
- Deploy to cloud (Kubernetes, Cloud Composer, etc.)
- Set up CI/CD for DAG deployment