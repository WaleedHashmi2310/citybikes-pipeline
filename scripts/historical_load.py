#!/usr/bin/env python3
"""
Historical data generation for CityBikes Pipeline.

Generates realistic historical station data for specified time range.
Extracts current station data once, then creates timestamped copies with
time-based availability patterns applied.

Usage:
    python scripts/historical_load.py [--start-date DATE] [--end-date DATE]
                                      [--days-back DAYS] [--interval-minutes MINUTES]
                                      [--networks NETWORKS] [--storage local|gcs]
                                      [--output-path PATH] [--bucket BUCKET] [--verbose]

Examples:
    # Generate data for last 7 days with 30-minute intervals
    python scripts/historical_load.py --days-back 7 --interval-minutes 30

    # Generate data for specific date range
    python scripts/historical_load.py --start-date 2026-03-20 --end-date 2026-03-27 --interval-minutes 60

    # Use specific networks and local storage
    python scripts/historical_load.py --days-back 3 --interval-minutes 120 --networks "callabike-berlin,stadtrad-hamburg-db" --storage local

Parameters:
    start_date: Start date for historical data (default: days_back from now)
    end_date: End date for historical data (default: current time)
    days_back: Number of days back from current time, starting at midnight UTC (default: 7)
    interval_minutes: Minutes between data points (default: 30)
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict
import math

# Add project root to path to import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.client import CityBikesClient
from ingestion.extractor import CityBikesExtractor
from ingestion.schemas import NormalizedStation
from storage.local import LocalStorage
from storage.gcs import GCSStorage
from storage.interface import StorageInterface

# Default network IDs (German cities from extractor - high volume networks)
DEFAULT_NETWORKS = [
    "callabike-frankfurt",
    "visa-frankfurt",
    "callabike-koln",
    "kvb-rad-koln",
    "nextbike-dusseldorf",
    "stadtrad-hamburg-db",
    "callabike-munchen",
    "stadtrad-stuttgart",
    "mobibike-dresden",
    "nextbike-leipzig",
    "callabike-berlin",
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

def get_time_pattern_adjustment(dt: datetime, city: str) -> float:
    """
    Calculate bike availability adjustment factor based on time of day and day of week.

    Returns multiplier between 0.3 (low availability) and 0.8 (high availability).

    Patterns:
    - Peak hours (7-9 AM, 4-7 PM): Lower availability (30-40%)
    - Night hours (0-5 AM): Higher availability (70-80%)
    - Weekends: Different peak patterns (midday/afternoon)
    - Major cities have lower peak availability

    Args:
        dt: Datetime to evaluate
        city: City name for size adjustment

    Returns:
        Adjustment factor (0.3 to 0.8)
    """
    hour = dt.hour
    minute = dt.minute
    day_of_week = dt.weekday()  # 0 = Monday, 6 = Sunday

    # Base adjustment based on hour
    if 0 <= hour < 5:  # Night hours
        base_adjustment = 0.7 + (hour / 20.0)  # 0.7 to 0.75
    elif 7 <= hour < 9:  # Morning peak
        base_adjustment = 0.3 + ((hour - 7) / 10.0)  # 0.3 to 0.5
    elif 16 <= hour < 19:  # Evening peak
        base_adjustment = 0.35 + ((hour - 16) / 15.0)  # 0.35 to 0.55
    else:
        # Daytime non-peak
        base_adjustment = 0.5 + (abs(hour - 12) / 48.0)  # 0.5 to 0.75

    # Weekend adjustments
    if day_of_week >= 5:  # Saturday (5) or Sunday (6)
        if 12 <= hour < 18:  # Weekend afternoon peak
            base_adjustment = max(0.3, base_adjustment - 0.2)
        else:
            base_adjustment = min(0.8, base_adjustment + 0.1)

    # City size adjustments - major cities have lower availability
    major_cities = ["Berlin", "Hamburg", "München", "Köln", "Frankfurt"]
    if city in major_cities:
        base_adjustment = max(0.25, base_adjustment - 0.1)

    # Add minute-based slight variation
    minute_variation = (math.sin(minute * 0.1047) * 0.05)  # +/- 5% based on minutes
    final_adjustment = max(0.25, min(0.85, base_adjustment + minute_variation))

    return final_adjustment

def generate_historical_records(
    base_stations: List[NormalizedStation],
    start_dt: datetime,
    end_dt: datetime,
    interval_minutes: int,
    storage: StorageInterface,
    logger: logging.Logger
) -> int:
    """
    Generate historical records for time range.

    Args:
        base_stations: Current station data to use as baseline
        start_dt: Start datetime (inclusive)
        end_dt: End datetime (exclusive)
        interval_minutes: Minutes between data points
        storage: Storage backend
        logger: Logger instance

    Returns:
        Total number of generated records
    """
    total_records = 0
    current_dt = start_dt

    # Group stations by city for efficiency
    stations_by_city: Dict[str, List[NormalizedStation]] = {}
    for station in base_stations:
        city = station.city
        if city not in stations_by_city:
            stations_by_city[city] = []
        stations_by_city[city].append(station)

    logger.info(f"Generating historical data from {start_dt} to {end_dt} "
                f"with {interval_minutes}-minute intervals")
    logger.info(f"Processing {len(base_stations)} base stations across {len(stations_by_city)} cities")

    while current_dt < end_dt:
        time_batch = []

        for city, city_stations in stations_by_city.items():
            adjustment = get_time_pattern_adjustment(current_dt, city)

            for station in city_stations:
                # Adjust free_bikes and empty_slots based on time pattern
                capacity = station.slots or (station.free_bikes + station.empty_slots)
                if capacity > 0:
                    adjusted_bikes = int(capacity * adjustment)
                    adjusted_bikes = max(0, min(capacity, adjusted_bikes))
                    adjusted_slots = capacity - adjusted_bikes
                else:
                    adjusted_bikes = station.free_bikes
                    adjusted_slots = station.empty_slots

                # Create new timestamp strings
                station_ts = current_dt.isoformat()
                ingestion_ts = current_dt  # Same as station timestamp for historical data

                historical_station = NormalizedStation(
                    id=station.station_id,
                    name=station.name,
                    latitude=station.latitude,
                    longitude=station.longitude,
                    free_bikes=adjusted_bikes,
                    empty_slots=adjusted_slots,
                    slots=station.slots,  # Keep original capacity
                    timestamp=station_ts,
                    ingestion_timestamp=ingestion_ts,
                    city=city,
                    extra=station.extra,
                )
                time_batch.append(historical_station)

        # Store batch
        if time_batch:
            storage_path = storage.store_stations(time_batch)
            total_records += len(time_batch)
            logger.debug(f"Stored {len(time_batch)} records for {current_dt} at {storage_path}")

        # Progress logging
        if total_records % 10000 == 0 and total_records > 0:
            logger.info(f"Generated {total_records} records so far...")

        # Move to next interval
        current_dt += timedelta(minutes=interval_minutes)

    return total_records

def main():
    parser = argparse.ArgumentParser(
        description="Generate historical CityBikes station data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Time range arguments
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument(
        "--start-date",
        type=str,
        help="Start date for historical data (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). "
             "If not provided, uses --days-back from now."
    )
    time_group.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="Number of days back from current time, starting at midnight UTC (default: 7)"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for historical data (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). "
             "Default: current time."
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=30,
        help="Minutes between data points (default: 30)"
    )

    # Network and storage arguments
    parser.add_argument(
        "--networks",
        type=str,
        help="Comma-separated list of network IDs to extract (default: all German cities)"
    )
    parser.add_argument(
        "--storage",
        choices=["local", "gcs"],
        help="Storage backend (default: local). Overrides STORAGE_BACKEND env var."
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
        "--clear-existing",
        action="store_true",
        help="Clear existing data in output path before generating"
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
    logger.info("Starting historical data generation")
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

    # Clear existing data if requested
    if args.clear_existing and hasattr(storage, 'clear'):
        logger.info("Clearing existing data...")
        storage.clear()  # type: ignore

    # Parse time range
    now = datetime.now(timezone.utc)

    if args.start_date:
        try:
            start_dt = datetime.fromisoformat(args.start_date.replace('Z', '+00:00'))
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error(f"Invalid start-date format: {args.start_date}")
            sys.exit(1)
    else:
        # Start from midnight (00:00:00) of the day that is days_back days ago
        start_dt = now - timedelta(days=args.days_back)
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    if args.end_date:
        try:
            end_dt = datetime.fromisoformat(args.end_date.replace('Z', '+00:00'))
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error(f"Invalid end-date format: {args.end_date}")
            sys.exit(1)
    else:
        end_dt = now

    # Validate time range
    if start_dt >= end_dt:
        logger.error(f"Start date {start_dt} must be before end date {end_dt}")
        sys.exit(1)

    if start_dt > now:
        logger.warning(f"Start date {start_dt} is in the future, adjusting to now")
        start_dt = now

    # Calculate total intervals
    total_seconds = (end_dt - start_dt).total_seconds()
    total_intervals = int(total_seconds / (args.interval_minutes * 60))

    logger.info(f"Time range: {start_dt} to {end_dt}")
    logger.info(f"Interval: {args.interval_minutes} minutes")
    logger.info(f"Total time points: {total_intervals}")

    # Override extractor's network list via subclass
    class CustomExtractor(CityBikesExtractor):
        GERMAN_NETWORK_IDS = networks

    # Initialize pipeline components
    try:
        client = CityBikesClient()
        extractor = CustomExtractor(client=client)

        # Test API connection
        logger.info("Testing API connection...")
        if not client.test_connection():
            logger.error("API connection test failed")
            sys.exit(1)
        logger.info("API connection successful")

        # Extract current station data once
        logger.info("Extracting current station data as baseline...")
        base_stations = extractor.extract_all_stations()

        if not base_stations:
            logger.error("No stations extracted")
            sys.exit(1)

        logger.info(f"Extracted {len(base_stations)} current stations")

        # Generate historical data
        total_records = generate_historical_records(
            base_stations=base_stations,
            start_dt=start_dt,
            end_dt=end_dt,
            interval_minutes=args.interval_minutes,
            storage=storage,
            logger=logger
        )

        logger.info(f"Historical data generation complete!")
        logger.info(f"Generated {total_records} total records")
        logger.info(f"Time range: {start_dt} to {end_dt}")
        logger.info(f"Interval: {args.interval_minutes} minutes")

        # Estimate file count
        cities = set(s.city for s in base_stations)
        logger.info(f"Coverage: {len(cities)} cities, {len(networks)} networks")

    except KeyboardInterrupt:
        logger.warning("Historical generation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Historical generation failed: {e}", exc_info=args.verbose)
        sys.exit(1)

if __name__ == "__main__":
    main()