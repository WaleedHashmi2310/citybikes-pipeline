# Terraform Infrastructure for CityBikes Pipeline

This directory contains Terraform configurations to provision cloud infrastructure for the CityBikes data pipeline on Google Cloud Platform.

## Overview

The Terraform configuration creates:
- **GCS bucket**: For storing raw Parquet data (partitioned by date/city)
- **BigQuery dataset**: For staging and mart tables
- **IAM service account**: With permissions for pipeline operations

## Modules

### `modules/gcs`
Creates a Google Cloud Storage bucket with uniform bucket-level access.

**Inputs:**
- `bucket_name` (required): Globally unique bucket name
- `project_id` (required): GCP project ID
- `location` (optional): Bucket location (default: `"EU"`)
- `storage_class` (optional): Storage class (default: `"STANDARD"`)
- `versioning_enabled` (optional): Enable versioning (default: `false`)
- `force_destroy` (optional): Force destroy bucket with contents (default: `false`)
- `lifecycle_rules` (optional): List of lifecycle rule configurations
- `labels` (optional): Resource labels map

**Outputs:**
- `bucket_name`: Name of the created bucket
- `self_link`: URI of the bucket
- `url`: GS URL (`gs://<bucket-name>`)

### `modules/bigquery`
Creates a BigQuery dataset for data warehouse.

**Inputs:**
- `dataset_id` (required): Dataset ID
- `project_id` (required): GCP project ID
- `location` (optional): Dataset location (default: `"EU"`)
- `friendly_name` (optional): Human-readable name
- `description` (optional): Dataset description
- `default_table_expiration_ms` (optional): Default table expiration in ms
- `delete_contents_on_destroy` (optional): Delete contents on destroy (default: `false`)
- `labels` (optional): Resource labels map

**Outputs:**
- `dataset_id`: ID of the created dataset
- `self_link`: URI of the dataset

### `modules/iam`
Creates a service account with necessary IAM roles.

**Inputs:**
- `service_account_id` (required): Service account ID
- `project_id` (required): GCP project ID
- `display_name` (optional): Display name
- `description` (optional): Description

**Outputs:**
- `service_account_email`: Email address of the service account

**IAM roles assigned:**
- `roles/storage.objectAdmin` (read/write/delete objects)
- `roles/storage.objectViewer` (read objects)
- `roles/bigquery.dataEditor` (edit datasets/tables)
- `roles/bigquery.jobUser` (run BigQuery jobs)

## Usage

### 1. Configure variables
Copy `terraform.tfvars.example` to `terraform.tfvars` and fill in your values:

```hcl
project_id          = "your-gcp-project-id"
region              = "europe-west1"
bucket_name         = "your-unique-bucket-name"
dataset_id          = "citybikes"
service_account_id  = "citybikes-pipeline-sa"
environment         = "dev"
```

### 2. Initialize Terraform
```bash
make terraform-init
```

### 3. Plan and apply
```bash
make terraform-plan
make terraform-apply
```

### 4. Update environment variables
After applying, note the outputs and update your `.env` file:

```bash
make terraform-output
```

Required environment variables for cloud mode:
- `GCS_BUCKET_NAME` (bucket name output)
- `DBT_BIGQUERY_PROJECT` (project_id)
- `DBT_BIGQUERY_DATASET` (dataset_id output)
- `GOOGLE_APPLICATION_CREDENTIALS` (path to service account key file)

### 5. Create service account key
The Terraform module creates a service account but does not generate a key file. Create a key manually via Google Cloud Console or CLI:

```bash
gcloud iam service-accounts keys create key.json \
  --iam-account $(terraform output -raw service_account_email)
```

Set `GOOGLE_APPLICATION_CREDENTIALS` to the key file path.

## Module Dependencies

No explicit dependencies between modules. All resources are created in parallel.

## Cleanup

To destroy all created resources:

```bash
make terraform-destroy
```

**Warning:** This will delete the GCS bucket (and all objects) and BigQuery dataset (if `delete_contents_on_destroy` is true).