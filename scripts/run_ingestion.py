#!/usr/bin/env python3
"""
CityBikes Pipeline Ingestion Script

Run data ingestion from CityBikes API to configured storage backend.
Supports local Parquet files and Google Cloud Storage.

Usage:
    python scripts/run_ingestion.py [--storage local|gcs] [--networks network1,network2]
                                    [--output-path PATH] [--bucket BUCKET] [--verbose]

Environment variables (override via .env):
    STORAGE_BACKEND: "local" or "gcs" (default: local)
    CITYBIKES_NETWORKS: comma-separated network IDs (default: German cities)
    GCS_BUCKET_NAME: bucket name for GCS storage
    GOOGLE_APPLICATION_CREDENTIALS: path to service account key JSON
    DBT_DUCKDB_PATH: path to DuckDB database (optional)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path to import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.client import CityBikesClient
from ingestion.extractor import CityBikesExtractor
from ingestion.loader import DataLoader
from storage.local import LocalStorage
from storage.gcs import GCSStorage
from storage.interface import StorageInterface  # noqa: F401

# Default network IDs (German cities from extractor)
DEFAULT_NETWORKS = [
    "callabike-frankfurt",
    "callabike-koln",
    "nextbike-dusseldorf",
    "stadtrad-hamburg-db",
    "callabike-munchen",
    "stadtrad-stuttgart",
    "mobibike-dresden",
    "nextbike-leipzig",
    "mvg-meinrad-nextbike-mainz",
]

def setup_logging(verbose: bool = False):
    """Configure logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Reduce noise from third-party libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

def parse_networks(networks_str: str) -> list[str]:
    """Parse comma-separated network IDs string."""
    if not networks_str:
        return DEFAULT_NETWORKS
    return [n.strip() for n in networks_str.split(",") if n.strip()]

def create_storage(args: argparse.Namespace, env_storage: str) -> tuple[StorageInterface, str]:
    """Instantiate storage backend based on arguments and environment."""
    # Determine storage type: command line argument > environment variable > default local
    storage_type = args.storage or env_storage or "local"

    if storage_type == "local":
        output_path = args.output_path or "./data/raw"
        storage = LocalStorage(base_path=output_path)
        storage_info = f"Local storage at {output_path}"
    elif storage_type == "gcs":
        bucket_name = args.bucket or os.getenv("GCS_BUCKET_NAME")
        if not bucket_name:
            raise ValueError(
                "GCS bucket name must be provided via --bucket argument "
                "or GCS_BUCKET_NAME environment variable"
            )
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        storage = GCSStorage(bucket_name=bucket_name, credentials_path=credentials_path)
        storage_info = f"GCS storage in bucket {bucket_name}"
    else:
        raise ValueError(f"Unsupported storage backend: {storage_type}")

    return storage, storage_info

def main():
    parser = argparse.ArgumentParser(
        description="CityBikes API data ingestion pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--storage",
        choices=["local", "gcs"],
        help="Storage backend (default: local). Overrides STORAGE_BACKEND env var."
    )
    parser.add_argument(
        "--networks",
        type=str,
        help="Comma-separated list of network IDs to extract (default: German cities)"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        help="Base path for local storage (default: ./data/raw)"
    )
    parser.add_argument(
        "--bucket",
        type=str,
        help="GCS bucket name (required for gcs storage)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Log startup information
    logger.info("Starting CityBikes ingestion pipeline")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")

    # Parse networks
    networks = parse_networks(args.networks or os.getenv("CITYBIKES_NETWORKS", ""))
    logger.info(f"Target networks: {networks}")

    # Create storage backend
    env_storage = os.getenv("STORAGE_BACKEND", "").lower()
    try:
        storage, storage_info = create_storage(args, env_storage)
        logger.info(f"Storage backend: {storage_info}")
    except Exception as e:
        logger.error(f"Failed to initialize storage: {e}")
        sys.exit(1)

    # Override extractor's network list via subclass
    class CustomExtractor(CityBikesExtractor):
        GERMAN_NETWORK_IDS = networks

    # Initialize pipeline components
    try:
        client = CityBikesClient()
        extractor = CustomExtractor(client=client)
        loader = DataLoader(extractor=extractor, storage=storage)

        # Test API connection
        logger.info("Testing API connection...")
        if not client.test_connection():
            logger.error("API connection test failed")
            sys.exit(1)
        logger.info("API connection successful")

        # Run ingestion
        logger.info("Starting data extraction and storage...")
        stations, storage_path = loader.load_all_stations()

        if not stations:
            logger.warning("No stations were extracted")
            sys.exit(0)

        logger.info(f"Successfully extracted {len(stations)} stations")
        logger.info(f"Data stored at: {storage_path}")

    except KeyboardInterrupt:
        logger.warning("Ingestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=args.verbose)
        sys.exit(1)

if __name__ == "__main__":
    main()