#!/usr/bin/env python3
"""
Generate environment variables for GCP deployment from Terraform outputs.

Usage:
    python scripts/generate_gcp_env.py [--prefix PREFIX] [--format {bash,yaml}]

Outputs environment variables in shell format (suitable for export) or YAML environment format.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Map Terraform output names to environment variable names
OUTPUT_MAPPING = {
    "project_id": "DBT_BIGQUERY_PROJECT",
    "region": "DBT_BIGQUERY_LOCATION",
    "bucket_name": "GCS_BUCKET_NAME",
    "dataset_id": "DBT_BIGQUERY_DATASET",
    "service_account_email": "SERVICE_ACCOUNT_EMAIL",
    # bucket_url is optional
}

def get_terraform_outputs():
    """Run terraform output -json and return parsed dict."""
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=Path(__file__).parent.parent / "terraform",
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running terraform: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing terraform output: {e}", file=sys.stderr)
        sys.exit(1)

def generate_env_vars(outputs, prefix=""):
    """Generate environment variable dictionary from Terraform outputs."""
    env_vars = {}
    for tf_key, env_key in OUTPUT_MAPPING.items():
        if tf_key in outputs:
            value = outputs[tf_key].get("value", "")
            if value:
                env_vars[f"{prefix}{env_key}"] = value
    return env_vars

def format_bash(env_vars):
    """Format environment variables as bash export statements."""
    lines = []
    for key, value in sorted(env_vars.items()):
        # Escape single quotes in value
        escaped_value = value.replace("'", "'\"'\"'")
        lines.append(f"export {key}='{escaped_value}'")
    return "\n".join(lines)

def format_yaml(env_vars):
    """Format environment variables as YAML environment snippet."""
    lines = ["env:"]
    for key, value in sorted(env_vars.items()):
        lines.append(f"  - {key}={value}")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Generate environment variables from Terraform outputs"
    )
    parser.add_argument(
        "--prefix", default="",
        help="Prefix to add to environment variable names"
    )
    parser.add_argument(
        "--format", choices=["bash", "yaml"], default="bash",
        help="Output format (default: bash)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    args = parser.parse_args()

    outputs = get_terraform_outputs()
    env_vars = generate_env_vars(outputs, prefix=args.prefix)

    if args.format == "bash":
        content = format_bash(env_vars)
    else:
        content = format_yaml(env_vars)

    if args.output:
        with open(args.output, "w") as f:
            f.write(content + "\n")
        print(f"Environment variables written to {args.output}", file=sys.stderr)
    else:
        print(content)

if __name__ == "__main__":
    main()