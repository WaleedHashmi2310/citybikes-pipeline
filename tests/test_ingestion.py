"""Unit tests for ingestion layer."""

import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch
import pytest
import requests
from ingestion.schemas import (
    Location,
    NetworkSummary,
    NetworkListResponse,
    StationExtra,
    Station,
    NetworkDetails,
    NormalizedStation,
)
from ingestion.client import CityBikesClient
from ingestion.extractor import CityBikesExtractor


# Sample test data
SAMPLE_LOCATION = {
    "city": "Frankfurt",
    "country": "DE",
    "latitude": 50.1109,
    "longitude": 8.6821,
}

SAMPLE_NETWORK_SUMMARY = {
    "id": "callabike-frankfurt",
    "name": "Call-A-Bike",
    "href": "/v2/networks/callabike-frankfurt",
    "company": "Call-A-Bike GmbH",
    "location": SAMPLE_LOCATION,
    "gbfs_href": "https://api.citybik.es/gbfs/v2/en/gbfs.json",
    "ebikes": True,
}

SAMPLE_STATION_EXTRA = {
    "uid": "123",
    "renting": "1",
    "returning": "1",
    "last_updated": "2024-01-01T12:00:00Z",
    "has_ebikes": True,
    "ebikes": "5",
    "payment": ["creditcard", "app"],
    "payment-terminal": True,
    "slots": "20",
    "rental_uris": {"android": "uri://android", "ios": "uri://ios"},
}

SAMPLE_STATION = {
    "id": "station_123",
    "name": "Hauptbahnhof",
    "latitude": 50.1109,
    "longitude": 8.6821,
    "timestamp": "2024-01-01T12:00:00Z",
    "free_bikes": 10,
    "empty_slots": 5,
    "extra": SAMPLE_STATION_EXTRA,
}

SAMPLE_NETWORK_DETAILS = {
    "id": "callabike-frankfurt",
    "name": "Call-A-Bike",
    "href": "/v2/networks/callabike-frankfurt",
    "company": "Call-A-Bike GmbH",
    "location": SAMPLE_LOCATION,
    "gbfs_href": "https://api.citybik.es/gbfs/v2/en/gbfs.json",
    "ebikes": True,
    "stations": [SAMPLE_STATION],
    "vehicles": [],
}


class TestSchemas:
    """Test Pydantic schemas."""

    def test_location_schema(self):
        """Test Location schema validation."""
        location = Location(**SAMPLE_LOCATION)
        assert location.city == "Frankfurt"
        assert location.country == "DE"
        assert location.latitude == 50.1109

    def test_network_summary_schema(self):
        """Test NetworkSummary schema validation."""
        network = NetworkSummary(**SAMPLE_NETWORK_SUMMARY)
        assert network.id == "callabike-frankfurt"
        assert network.name == "Call-A-Bike"
        assert isinstance(network.location, Location)

    def test_station_extra_schema(self):
        """Test StationExtra schema with various input types."""
        # Test with string numeric fields
        extra = StationExtra(**SAMPLE_STATION_EXTRA)
        assert extra.uid == "123"
        assert extra.renting == "1"
        assert extra.last_updated == "2024-01-01T12:00:00Z"
        assert extra.payment_terminal is True

        # Test with integer numeric fields
        int_extra_data = SAMPLE_STATION_EXTRA.copy()
        int_extra_data.update({
            "renting": 1,
            "returning": 1,
            "last_updated": 1678901234,
            "ebikes": 5,
            "slots": 20,
        })
        extra = StationExtra(**int_extra_data)
        assert extra.renting == 1
        assert extra.last_updated == 1678901234

    def test_station_schema(self):
        """Test Station schema validation."""
        station = Station(**SAMPLE_STATION)
        assert station.id == "station_123"
        assert station.name == "Hauptbahnhof"
        assert station.free_bikes == 10
        assert isinstance(station.extra, StationExtra)

    def test_network_details_schema(self):
        """Test NetworkDetails schema validation."""
        details = NetworkDetails(**SAMPLE_NETWORK_DETAILS)
        assert details.id == "callabike-frankfurt"
        assert len(details.stations) == 1
        assert details.stations[0].name == "Hauptbahnhof"

    def test_normalized_station_schema(self):
        """Test NormalizedStation schema validation."""
        station_data = {
            "id": "station_123",
            "name": "Hauptbahnhof",
            "latitude": 50.1109,
            "longitude": 8.6821,
            "free_bikes": 10,
            "empty_slots": 5,
            "timestamp": "2024-01-01T12:00:00Z",
            "ingestion_timestamp": datetime.now(timezone.utc),
            "city": "Frankfurt",
        }
        station = NormalizedStation(**station_data)
        assert station.station_id == "station_123"
        assert station.city == "Frankfurt"
        assert station.ingestion_timestamp.tzinfo == timezone.utc


class TestCityBikesClient:
    """Test CityBikesClient."""

    @patch("ingestion.client.requests.Session")
    def test_get_networks_success(self, mock_session_class):
        """Test successful networks fetch."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"networks": [SAMPLE_NETWORK_SUMMARY]}
        mock_response.headers = {}
        mock_response.raise_for_status.return_value = None

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = CityBikesClient()
        result = client.get_networks()

        assert len(result.networks) == 1
        assert result.networks[0].id == "callabike-frankfurt"
        mock_session.get.assert_called_once_with(
            "https://api.citybik.es/v2/networks", timeout=10
        )

    @patch("ingestion.client.requests.Session")
    def test_get_network_details_success(self, mock_session_class):
        """Test successful network details fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {"network": SAMPLE_NETWORK_DETAILS}
        mock_response.headers = {}
        mock_response.raise_for_status.return_value = None

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = CityBikesClient()
        result = client.get_network_details("callabike-frankfurt")

        assert result.id == "callabike-frankfurt"
        assert len(result.stations) == 1
        mock_session.get.assert_called_once_with(
            "https://api.citybik.es/v2/networks/callabike-frankfurt", timeout=10
        )

    @patch("ingestion.client.requests.Session")
    def test_retry_logic_on_connection_error(self, mock_session_class):
        """Test retry logic on connection error."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.ConnectionError
        mock_session_class.return_value = mock_session

        client = CityBikesClient()
        with pytest.raises(requests.exceptions.ConnectionError):
            client.get_networks()

        # Should retry 3 times (initial + 2 retries)
        assert mock_session.get.call_count == 3

    def test_test_connection_success(self):
        """Test connection test method with successful connection."""
        with patch.object(CityBikesClient, "_make_request") as mock_make_request:
            mock_make_request.return_value = Mock()
            client = CityBikesClient()
            assert client.test_connection() is True

    def test_test_connection_failure(self):
        """Test connection test method with failed connection."""
        with patch.object(CityBikesClient, "_make_request") as mock_make_request:
            mock_make_request.side_effect = requests.exceptions.RequestException
            client = CityBikesClient()
            assert client.test_connection() is False


class TestCityBikesExtractor:
    """Test CityBikesExtractor."""

    def test_extractor_initialization(self):
        """Test extractor initialization with and without client."""
        # With default client
        extractor = CityBikesExtractor()
        assert extractor.client is not None

        # With custom client
        mock_client = Mock()
        extractor = CityBikesExtractor(client=mock_client)
        assert extractor.client is mock_client

    def test_german_network_ids(self):
        """Test that German network IDs are correctly defined."""
        extractor = CityBikesExtractor()
        ids = extractor.GERMAN_NETWORK_IDS

        assert len(ids) == 9
        assert "callabike-frankfurt" in ids
        assert "nextbike-dusseldorf" in ids
        assert "stadtrad-hamburg-db" in ids
        assert "callabike-munchen" in ids
        assert "stadtrad-stuttgart" in ids
        assert "mobibike-dresden" in ids
        assert "nextbike-leipzig" in ids
        assert "mvg-meinrad-nextbike-mainz" in ids

    @patch.object(CityBikesClient, "get_network_details")
    def test_extract_network_stations_success(self, mock_get_details):
        """Test successful station extraction for a single network."""
        # Mock network details response
        mock_details = NetworkDetails(**SAMPLE_NETWORK_DETAILS)
        mock_get_details.return_value = mock_details

        extractor = CityBikesExtractor()
        stations = extractor.extract_network_stations("callabike-frankfurt")

        assert len(stations) == 1
        station = stations[0]
        assert station.station_id == "station_123"
        assert station.city == "Frankfurt"
        assert station.ingestion_timestamp.tzinfo == timezone.utc

        mock_get_details.assert_called_once_with("callabike-frankfurt")

    @patch.object(CityBikesClient, "get_network_details")
    @patch("ingestion.extractor.logger")
    def test_extract_network_stations_with_normalization_error(
        self, mock_logger, mock_get_details
    ):
        """Test extraction when station normalization fails."""
        # Mock network details with valid stations
        mock_details = NetworkDetails(**SAMPLE_NETWORK_DETAILS)
        mock_get_details.return_value = mock_details

        # Make NormalizedStation constructor raise an exception for the first station
        from ingestion.schemas import NormalizedStation as NormStation
        original_init = NormStation.__init__

        def faulty_init(self, *args, **kwargs):
            # Check if this is the station we want to fail
            if kwargs.get("id") == "station_123":
                raise ValueError("Test normalization error")
            return original_init(self, *args, **kwargs)

        extractor = CityBikesExtractor()
        with patch.object(NormStation, "__init__", faulty_init):
            stations = extractor.extract_network_stations("callabike-frankfurt")

        # Should have zero stations (the only station failed)
        assert len(stations) == 0
        # Should have logged an error
        assert mock_logger.error.call_count == 1

    @patch.object(CityBikesExtractor, "extract_network_stations")
    @patch("ingestion.extractor.logger")
    def test_extract_all_stations(self, mock_logger, mock_extract_network):
        """Test extraction from all networks."""
        # Mock successful extraction for first network, failure for second
        mock_extract_network.side_effect = [
            [Mock(spec=NormalizedStation), Mock(spec=NormalizedStation)],  # First network
            Exception("API error"),  # Second network fails
            [Mock(spec=NormalizedStation)],  # Third network succeeds
        ]

        extractor = CityBikesExtractor()
        extractor.GERMAN_NETWORK_IDS = ["net1", "net2", "net3"]  # Shorter list for test

        stations = extractor.extract_all_stations()

        # Should have stations from successful networks
        assert len(stations) == 3
        # Should have logged one error for failed network
        assert mock_logger.error.call_count == 1