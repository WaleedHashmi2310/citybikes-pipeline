"""Data extraction from CityBikes API."""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from ingestion.client import CityBikesClient
from ingestion.schemas import NetworkDetails, NormalizedStation

logger = logging.getLogger(__name__)


class CityBikesExtractor:
    """Extract and normalize station data from CityBikes API."""

    # Primary network IDs for target German cities (high volume networks)
    GERMAN_NETWORK_IDS = [
        "callabike-frankfurt",  # Frankfurt
        "visa-frankfurt",  # Frankfurt (alternative, high volume)
        "callabike-koln",  # Cologne (Köln)
        "kvb-rad-koln",  # Cologne (alternative, high volume)
        "nextbike-dusseldorf",  # Dusseldorf (Düsseldorf)
        "stadtrad-hamburg-db",  # Hamburg
        "callabike-munchen",  # Munich (München)
        "stadtrad-stuttgart",  # Stuttgart
        "mobibike-dresden",  # Dresden
        "nextbike-leipzig",  # Leipzig
        "callabike-berlin",  # Berlin (added for high volume)
        "mvg-meinrad-nextbike-mainz",  # Mainz
        # Koblenz not available in CityBikes API
    ]

    def __init__(self, client: Optional[CityBikesClient] = None):
        """
        Initialize extractor.

        Args:
            client: CityBikesClient instance (creates new one if not provided)
        """
        self.client = client or CityBikesClient()

    def extract_network_stations(self, network_id: str) -> List[NormalizedStation]:
        """
        Extract and normalize stations for a single network.

        Args:
            network_id: Network identifier

        Returns:
            List of normalized station records

        Raises:
            requests.exceptions.HTTPError: For API errors
            ValidationError: If response doesn't match schema
        """
        logger.info(f"Extracting stations for network: {network_id}")

        # Fetch network details
        network_details: NetworkDetails = self.client.get_network_details(network_id)
        city = network_details.location.city
        ingestion_timestamp = datetime.now(timezone.utc)

        normalized_stations = []
        for station in network_details.stations:
            try:
                normalized = NormalizedStation(
                    id=station.id,
                    name=station.name,
                    latitude=station.latitude,
                    longitude=station.longitude,
                    free_bikes=station.free_bikes,
                    empty_slots=station.empty_slots,
                    timestamp=self._clean_timestamp(station.timestamp),
                    ingestion_timestamp=ingestion_timestamp,
                    city=city,
                )
                normalized_stations.append(normalized)
            except Exception as e:
                logger.error(
                    f"Failed to normalize station {station.id} in {network_id}: {e}"
                )
                # Continue with other stations
                continue

        logger.info(
            f"Extracted {len(normalized_stations)} stations from {network_id} ({city})"
        )
        return normalized_stations

    def _clean_timestamp(self, timestamp: str) -> str:
        """Clean timestamp string for DuckDB compatibility.

        Removes redundant 'Z' suffix when timezone offset already present.
        Example: '2026-03-24T09:23:54.828179+00:00Z' -> '2026-03-24T09:23:54.828179+00:00'
        """
        if timestamp.endswith('Z') and '+' in timestamp:
            return timestamp[:-1]
        return timestamp

    def extract_all_stations(self) -> List[NormalizedStation]:
        """
        Extract stations from all target German cities.

        Returns:
            List of normalized station records from all networks
        """
        all_stations = []
        successful = 0
        failed = 0

        for network_id in self.GERMAN_NETWORK_IDS:
            try:
                stations = self.extract_network_stations(network_id)
                all_stations.extend(stations)
                successful += 1
            except Exception as e:
                logger.error(f"Failed to extract stations for {network_id}: {e}")
                failed += 1
                # Continue with other networks
                continue

        logger.info(
            f"Extraction complete: {successful} networks successful, "
            f"{failed} failed, {len(all_stations)} total stations"
        )
        return all_stations
