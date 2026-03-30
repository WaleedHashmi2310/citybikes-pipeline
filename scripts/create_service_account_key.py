#!/usr/bin/env python3
"""
Create a service account key for the CityBikes pipeline service account.

Usage:
    python scripts/create_service_account_key.py [--output FILE] [--project PROJECT_ID]

Creates a service account key file and updates .env with DBT_BIGQUERY_KEYFILE and
GOOGLE_APPLICATION_CREDENTIALS variables pointing to the key file.

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

def update_env_file(key_file, env_file=".env"):
    """Update .env file with key file path for DBT_BIGQUERY_KEYFILE and GOOGLE_APPLICATION_CREDENTIALS."""
    env_path = Path(env_file) if Path(env_file).is_absolute() else Path(__file__).parent.parent / env_file
    existing_lines = []
    updated_vars = set()

    # Variables to update
    vars_to_update = {
        "DBT_BIGQUERY_KEYFILE": key_file
    }

    # Read existing .env file if it exists
    if env_path.exists():
        with open(env_path, "r") as f:
            existing_lines = f.readlines()

    # Process each line, updating variables that match
    new_lines = []
    for line in existing_lines:
        line = line.rstrip('\n')
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            new_lines.append(line)
            continue

        # Parse KEY=VALUE
        if '=' in line:
            key = line.split('=', 1)[0].strip()
            if key in vars_to_update:
                # Update this line with new value
                value = vars_to_update[key]
                value = str(value).replace('\n', '\\n').replace('\r', '\\r')
                new_lines.append(f"{key}={value}")
                updated_vars.add(key)
                continue

        # Keep line as-is
        new_lines.append(line)

    # Add any new variables that weren't in the file
    for key, value in sorted(vars_to_update.items()):
        if key not in updated_vars:
            value = str(value).replace('\n', '\\n').replace('\r', '\\r')
            new_lines.append(f"{key}={value}")

    # Write back to file
    with open(env_path, "w") as f:
        f.write("\n".join(new_lines) + "\n")

    print(f"Updated .env file at {env_path} with key file path")
    return env_path

def print_deployment_instructions(key_file, service_account_email):
    """Print instructions for using the service account key in GCP deployments."""
    print("\n" + "="*60)
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

    # Update .env file with key file path
    update_env_file(args.output)

    # Print instructions
    print_deployment_instructions(args.output, service_account_email)

if __name__ == "__main__":
    main()