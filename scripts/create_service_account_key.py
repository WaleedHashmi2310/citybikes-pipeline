#!/usr/bin/env python3
"""
Create a service account key for the CityBikes pipeline service account.

Usage:
    python scripts/create_service_account_key.py [--output FILE] [--project PROJECT_ID]

Requires gcloud CLI to be installed and authenticated.
"""

import argparse
import subprocess
import sys
from pathlib import Path

def get_terraform_output(output_name):
    """Get a Terraform output value."""
    try:
        result = subprocess.run(
            ["terraform", "output", "-raw", output_name],
            cwd=Path(__file__).parent.parent / "terraform",
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting Terraform output {output_name}: {e}", file=sys.stderr)
        sys.exit(1)

def create_service_account_key(service_account_email, output_file, project_id=None):
    """Create a new service account key using gcloud."""
    cmd = [
        "gcloud", "iam", "service-accounts", "keys", "create",
        output_file,
        "--iam-account", service_account_email,
    ]
    if project_id:
        cmd.extend(["--project", project_id])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Service account key created: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating service account key: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: gcloud CLI not found. Please install Google Cloud SDK.", file=sys.stderr)
        sys.exit(1)

def print_deployment_instructions(key_file, service_account_email):
    """Print instructions for using the service account key in GCP deployments."""
    print("\n" + "="*60)
    print("GCP Deployment Instructions")
    print("="*60)
    print(f"\nService account key created: {key_file}")
    print(f"Service account email: {service_account_email}")
    print("\nChoose one of these deployment options (see README.md for details):")
    print("\nOption 1: Compute Engine VM (Cheapest ~$15/month)")
    print("  - Deploy Docker Compose setup to a small Compute Engine instance")
    print("  - Copy the key file to the VM and set GOOGLE_APPLICATION_CREDENTIALS")
    print("  - Use environment variables from generate_gcp_env.py")
    print("\nOption 2: Cloud Run Jobs + Cloud Scheduler (Pay-per-use)")
    print("  - Containerize each task (ingestion, dbt run, dbt test)")
    print("  - Mount the key as a secret in Cloud Run")
    print("  - Trigger jobs via Cloud Scheduler")
    print("\nOption 3: GKE Autopilot (~$50-100/month)")
    print("  - Deploy Airflow Helm chart on managed Kubernetes")
    print("  - Create a Kubernetes secret from the key file")
    print("  - Set environment variables in pod spec")
    print("\nCommon setup steps:")
    print("  1. Set environment variables for cloud execution:")
    print("     export STORAGE_BACKEND=gcs")
    print("     export DBT_TARGET=prod")
    print("     source <(python scripts/generate_gcp_env.py --format bash)")
    print("  2. Configure authentication:")
    print("     export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/{key_file}")
    print("  3. Verify permissions: the service account has roles for GCS and BigQuery")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(
        description="Create service account key for CityBikes pipeline"
    )
    parser.add_argument(
        "--output", "-o",
        default="citybikes-pipeline-sa-key.json",
        help="Output file for service account key (default: citybikes-pipeline-sa-key.json)"
    )
    parser.add_argument(
        "--project",
        help="Google Cloud project ID (default: from Terraform)"
    )
    args = parser.parse_args()

    # Get service account email from Terraform
    print("Fetching service account email from Terraform...")
    service_account_email = get_terraform_output("service_account_email")

    # Get project ID
    if args.project:
        project_id = args.project
    else:
        project_id = get_terraform_output("project_id")

    print(f"Service account: {service_account_email}")
    print(f"Project ID: {project_id}")
    print(f"Output file: {args.output}")

    # Check if file already exists
    if Path(args.output).exists():
        print(f"Warning: File {args.output} already exists.", file=sys.stderr)
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            sys.exit(0)

    # Create key
    create_service_account_key(service_account_email, args.output, project_id)

    # Print instructions
    print_deployment_instructions(args.output, service_account_email)

if __name__ == "__main__":
    main()