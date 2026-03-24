#!/usr/bin/env python3
"""
Generate sample Parquet data for testing dbt staging models.
Uses the existing LocalStorage implementation.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path to import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.schemas import NormalizedStation
from storage.local import LocalStorage

def generate_sample_stations():
    """Generate sample station data."""
    now = datetime.now(timezone.utc)

    stations = [
        NormalizedStation(
            station_id="station_001",
            name="Hauptbahnhof",
            latitude=50.1109,
            longitude=8.6821,
            free_bikes=5,
            empty_slots=10,
            timestamp="2024-01-15T12:30:00Z",
            ingestion_timestamp=now,
            city="Frankfurt"
        ),
        NormalizedStation(
            station_id="station_002",
            name="Rathaus",
            latitude=50.115,
            longitude=8.684,
            free_bikes=3,
            empty_slots=7,
            timestamp="2024-01-15T12:30:00Z",
            ingestion_timestamp=now,
            city="Frankfurt"
        ),
        NormalizedStation(
            station_id="station_003",
            name="Domplatz",
            latitude=50.9414,
            longitude=6.9583,
            free_bikes=8,
            empty_slots=4,
            timestamp="2024-01-15T12:30:00Z",
            ingestion_timestamp=now,
            city="Cologne"
        ),
    ]
    return stations

def main():
    """Generate and store sample data."""
    print("Generating sample station data...")
    stations = generate_sample_stations()

    # Store using LocalStorage
    storage = LocalStorage(base_path="./data/raw")
    try:
        path = storage.store_stations(stations)
        print(f"Sample data written to: {path}")
        print(f"Partition directory: {Path(path).parent}")
    except Exception as e:
        print(f"Failed to store sample data: {e}")
        sys.exit(1)

    # List generated files
    raw_dir = project_root / "data" / "raw"
    print("\nGenerated files:")
    for file in raw_dir.rglob("*.parquet"):
        print(f"  {file.relative_to(raw_dir)}")

if __name__ == "__main__":
    main()