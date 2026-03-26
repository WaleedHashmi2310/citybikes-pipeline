#!/usr/bin/env python3
"""
Generate environment variables for GCP deployment from Terraform outputs.

Usage:
    python scripts/generate_gcp_env.py [--prefix PREFIX] [--format {bash,yaml,dotenv}]
                                       [--output FILE] [--update-env] [--env-file FILE]

Outputs environment variables in shell format (suitable for export), YAML environment format,
or .env format (KEY=VALUE). Use --update-env to update .env file with generated variables.
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

def format_dotenv(env_vars):
    """Format environment variables as .env file lines (KEY=VALUE)."""
    lines = []
    for key, value in sorted(env_vars.items()):
        # Escape newlines and handle special characters
        value = str(value).replace('\n', '\\n').replace('\r', '\\r')
        lines.append(f"{key}={value}")
    return "\n".join(lines)

def update_dotenv_file(env_vars, env_file=".env"):
    """Update or add environment variables in .env file."""
    env_path = Path(env_file) if Path(env_file).is_absolute() else Path(__file__).parent.parent / env_file
    existing_lines = []
    updated_vars = set()

    # Read existing .env file if it exists
    if env_path.exists():
        with open(env_path, "r") as f:
            existing_lines = f.readlines()

    # Process each line, updating variables that match our env_vars
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
            if key in env_vars:
                # Update this line with new value
                value = env_vars[key]
                value = str(value).replace('\n', '\\n').replace('\r', '\\r')
                new_lines.append(f"{key}={value}")
                updated_vars.add(key)
                continue

        # Keep line as-is
        new_lines.append(line)

    # Add any new variables that weren't in the file
    for key, value in sorted(env_vars.items()):
        if key not in updated_vars:
            value = str(value).replace('\n', '\\n').replace('\r', '\\r')
            new_lines.append(f"{key}={value}")

    # Write back to file
    with open(env_path, "w") as f:
        f.write("\n".join(new_lines) + "\n")

    print(f"Updated {len(env_vars)} variables in {env_path}", file=sys.stderr)
    return env_path

def main():
    parser = argparse.ArgumentParser(
        description="Generate environment variables from Terraform outputs"
    )
    parser.add_argument(
        "--prefix", default="",
        help="Prefix to add to environment variable names"
    )
    parser.add_argument(
        "--format", choices=["bash", "yaml", "dotenv"], default="bash",
        help="Output format (default: bash)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--update-env", action="store_true",
        help="Update .env file with generated variables"
    )
    parser.add_argument(
        "--env-file", default=".env",
        help="Path to .env file (default: .env)"
    )
    args = parser.parse_args()

    outputs = get_terraform_outputs()
    env_vars = generate_env_vars(outputs, prefix=args.prefix)

    # Update .env file if requested
    if args.update_env:
        env_path = update_dotenv_file(env_vars, env_file=args.env_file)
        # If no output specified, we're done
        if not args.output:
            return

    # Generate content in requested format
    if args.format == "bash":
        content = format_bash(env_vars)
    elif args.format == "yaml":
        content = format_yaml(env_vars)
    else:  # dotenv
        content = format_dotenv(env_vars)

    if args.output:
        with open(args.output, "w") as f:
            f.write(content + "\n")
        print(f"Environment variables written to {args.output}", file=sys.stderr)
    else:
        print(content)

if __name__ == "__main__":
    main()