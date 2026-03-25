"""Local Parquet storage implementation."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List
import itertools
import pandas as pd
from ingestion.schemas import NormalizedStation
from storage.interface import StorageInterface, StorageError

logger = logging.getLogger(__name__)


class LocalStorage(StorageInterface):
    """Store station data as partitioned Parquet files locally.

    Partitions data by date (from ingestion_timestamp) and city.
    Creates directory structure: base_path/city=CityName/date=YYYY-MM-DD/

    Args:
        base_path: Root directory for storage (default: "./data/raw")
    """

    def __init__(self, base_path: str = "./data/raw"):
        self.base_path = Path(base_path)
        logger.debug(f"Initialized LocalStorage with base path: {self.base_path}")

    def store_stations(self, stations: List[NormalizedStation]) -> str:
        """Store normalized stations as partitioned Parquet files.

        Args:
            stations: List of normalized station records

        Returns:
            Absolute path to stored Parquet file (first city's file)

        Raises:
            StorageError: If storage operation fails
        """
        if not stations:
            logger.warning("Empty stations list provided, nothing to store")
            return str(self.base_path)

        try:
            # Determine batch timestamp for file naming (use first station's ingestion time)
            batch_timestamp = stations[0].ingestion_timestamp
            batch_date = batch_timestamp.date()

            # Sort stations by city for grouping
            stations_sorted = sorted(stations, key=lambda s: s.city)

            # Group stations by city
            first_file_path = None
            city_count = 0

            for city, city_stations in itertools.groupby(stations_sorted, key=lambda s: s.city):
                city_count += 1
                city_stations_list = list(city_stations)

                # Convert to pandas DataFrame for this city
                df = self._stations_to_dataframe(city_stations_list)

                # Generate filename with timestamp and city (for uniqueness)
                filename = f"stations_{batch_timestamp.strftime('%Y%m%d_%H%M%S')}_{city}.parquet"

                # Full path with partitioning
                full_path = (
                    self.base_path / f"city={city}" / f"date={batch_date}"
                )

                # Ensure directory exists
                full_path.mkdir(parents=True, exist_ok=True)
                file_path = full_path / filename

                # Write Parquet file with partitioning
                logger.info(
                    f"Writing {len(city_stations_list)} stations to {file_path} "
                    f"(partitioned by city={city}, date={batch_date})"
                )
                df.to_parquet(file_path, index=False)

                logger.debug(f"Successfully wrote Parquet file: {file_path}")

                # Capture first file path to return
                if first_file_path is None:
                    first_file_path = file_path

            logger.info(f"Stored stations for {city_count} cities")
            # Return path to first city's file (for compatibility with tests and GCSStorage)
            return str(first_file_path.absolute())

        except Exception as e:
            logger.error(f"Failed to store stations locally: {e}")
            raise StorageError(f"Local storage failed: {e}") from e

    def _stations_to_dataframe(self, stations: List[NormalizedStation]) -> pd.DataFrame:
        """Convert list of NormalizedStation to pandas DataFrame.

        Adds partition columns for date and city.
        """
        # Convert to dict list
        station_dicts = []
        for station in stations:
            station_dict = station.model_dump(by_alias=True)
            # Ensure station_id field is present (alias for 'id')
            station_dict["station_id"] = station_dict.pop("id", station.station_id)
            # Add partition columns per station
            station_dict["city"] = station.city
            station_dict["date"] = station.ingestion_timestamp.date().isoformat()
            station_dicts.append(station_dict)

        df = pd.DataFrame(station_dicts)


        # Ensure consistent column order
        columns = [
            "station_id",
            "name",
            "latitude",
            "longitude",
            "free_bikes",
            "empty_slots",
            "timestamp",
            "ingestion_timestamp",
            "city",
            "date",
        ]
        # Keep only columns that exist
        existing_columns = [col for col in columns if col in df.columns]
        df = df[existing_columns]

        return df
