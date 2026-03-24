"""Unit tests for storage layer."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import pytest
from ingestion.schemas import NormalizedStation
from storage.interface import StorageInterface, StorageError
from storage.local import LocalStorage
from storage.gcs import GCSStorage, google_exceptions
from ingestion.loader import DataLoader
from ingestion.extractor import CityBikesExtractor


# Sample test data matching test_ingestion.py patterns
SAMPLE_STATIONS = [
    NormalizedStation(
        station_id="station_123",
        name="Hauptbahnhof",
        latitude=50.1109,
        longitude=8.6821,
        free_bikes=10,
        empty_slots=5,
        timestamp="2024-01-01T12:00:00Z",
        ingestion_timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        city="Frankfurt",
    ),
    NormalizedStation(
        station_id="station_456",
        name="Rathaus",
        latitude=50.115,
        longitude=8.684,
        free_bikes=3,
        empty_slots=7,
        timestamp="2024-01-01T12:00:00Z",
        ingestion_timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        city="Frankfurt",
    ),
]


class TestStorageInterface:
    """Test abstract storage interface."""

    def test_interface_is_abstract(self):
        """Test that StorageInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            StorageInterface()  # Should fail as abstract class

    def test_interface_requires_store_stations_method(self):
        """Test that subclasses must implement store_stations."""
        class ConcreteStorage(StorageInterface):
            def store_stations(self, stations):
                return "test"

        # Should not raise
        storage = ConcreteStorage()
        result = storage.store_stations([])
        assert result == "test"

    def test_interface_enforces_signature(self):
        """Test that store_stations accepts List[NormalizedStation]."""
        class ConcreteStorage(StorageInterface):
            def store_stations(self, stations: List[NormalizedStation]) -> str:
                return "ok"

        storage = ConcreteStorage()
        # Should accept empty list
        result = storage.store_stations([])
        assert result == "ok"


class TestLocalStorage:
    """Test local Parquet storage implementation."""

    def test_local_storage_initialization(self):
        """Test LocalStorage initialization with default and custom paths."""
        # Default path
        storage = LocalStorage()
        assert storage.base_path == Path("./data/raw")

        # Custom path
        custom_path = "/custom/data/path"
        storage = LocalStorage(base_path=custom_path)
        assert storage.base_path == Path(custom_path)

    def test_store_stations_empty_list(self):
        """Test storing empty stations list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)
            result = storage.store_stations([])
            assert result == str(Path(tmpdir))
            # No files should be created
            assert len(list(Path(tmpdir).rglob("*"))) == 0

    def test_store_stations_creates_partitioned_files(self):
        """Test that stations are stored as partitioned Parquet files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)
            result = storage.store_stations(SAMPLE_STATIONS)

            # Verify path exists
            result_path = Path(result)
            assert result_path.exists()
            assert result_path.suffix == ".parquet"

            # Verify partition directory structure
            parent_dir = result_path.parent
            assert parent_dir.name == "city=Frankfurt"
            assert parent_dir.parent.name == "date=2024-01-01"
            assert parent_dir.parent.parent == Path(tmpdir)

            # Verify file can be read back
            df = pd.read_parquet(result_path)
            assert len(df) == 2
            assert "station_id" in df.columns
            assert "city" in df.columns
            assert "date" in df.columns
            assert df["city"].iloc[0] == "Frankfurt"
            assert df["date"].iloc[0] == "2024-01-01"

    def test_store_stations_with_different_cities(self):
        """Test that stations with different cities are handled."""
        mixed_stations = [
            NormalizedStation(
                station_id="station_1",
                name="Test",
                latitude=0,
                longitude=0,
                free_bikes=1,
                empty_slots=1,
                timestamp="2024-01-01T12:00:00Z",
                ingestion_timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                city="City1",
            ),
            NormalizedStation(
                station_id="station_2",
                name="Test",
                latitude=0,
                longitude=0,
                free_bikes=1,
                empty_slots=1,
                timestamp="2024-01-01T12:00:00Z",
                ingestion_timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                city="City2",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)
            # Should use first station's city for partition
            result = storage.store_stations(mixed_stations)
            result_path = Path(result)
            assert "city=City1" in str(result_path)

    def test_store_stations_error_handling(self):
        """Test error handling during storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)

            # Create a read-only directory to cause permission error
            read_only_dir = Path(tmpdir) / "readonly"
            read_only_dir.mkdir()
            read_only_dir.chmod(0o444)

            storage.base_path = read_only_dir

            with pytest.raises(StorageError):
                storage.store_stations(SAMPLE_STATIONS)


class TestGCSStorage:
    """Test Google Cloud Storage implementation."""

    @patch("storage.gcs.GCS_AVAILABLE", True)
    @patch("storage.gcs.storage")
    def test_gcs_storage_initialization(self, mock_storage):
        """Test GCSStorage initialization."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket

        storage = GCSStorage(bucket_name="test-bucket", project_id="test-project")

        assert storage.bucket_name == "test-bucket"
        assert storage.project_id == "test-project"
        assert storage.client is mock_client
        assert storage.bucket is mock_bucket
        mock_storage.Client.assert_called_once_with(project="test-project")

    @patch("storage.gcs.GCS_AVAILABLE", True)
    @patch("storage.gcs.storage")
    def test_gcs_storage_with_credentials_path(self, mock_storage):
        """Test GCSStorage initialization with credentials path."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_storage.Client.from_service_account_json.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket

        storage = GCSStorage(
            bucket_name="test-bucket",
            credentials_path="/path/to/credentials.json",
            project_id="test-project",
        )

        mock_storage.Client.from_service_account_json.assert_called_once_with(
            "/path/to/credentials.json", project="test-project"
        )
        assert storage.bucket is mock_bucket

    @patch("storage.gcs.GCS_AVAILABLE", False)
    def test_gcs_storage_without_dependencies(self):
        """Test GCSStorage raises ImportError when google-cloud-storage not installed."""
        with pytest.raises(ImportError):
            GCSStorage(bucket_name="test-bucket")

    @patch("storage.gcs.GCS_AVAILABLE", True)
    @patch("storage.gcs.storage")
    @patch("storage.gcs.LocalStorage")
    def test_store_stations_to_gcs(self, mock_local_storage, mock_storage):
        """Test storing stations to GCS."""
        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        # Mock local storage
        mock_local = Mock()
        mock_local.store_stations.return_value = "/tmp/stations_20240101_120000.parquet"
        mock_local_storage.return_value = mock_local

        storage = GCSStorage(bucket_name="test-bucket")
        storage.local_storage = mock_local
        storage.bucket = mock_bucket

        result = storage.store_stations(SAMPLE_STATIONS)

        # Verify local storage was called
        mock_local.store_stations.assert_called_once_with(SAMPLE_STATIONS)

        # Verify upload was called with correct path
        mock_bucket.blob.assert_called_once_with(
            "raw/date=2024-01-01/city=Frankfurt/stations_20240101_120000.parquet"
        )
        mock_blob.upload_from_filename.assert_called_once_with("/tmp/stations_20240101_120000.parquet")

        # Verify result is GCS URI
        assert result == "gs://test-bucket/raw/date=2024-01-01/city=Frankfurt/stations_20240101_120000.parquet"

    @patch("storage.gcs.GCS_AVAILABLE", True)
    @patch("storage.gcs.storage")
    @patch("storage.gcs.LocalStorage")
    def test_store_stations_empty_list(self, mock_local_storage, mock_storage):
        """Test storing empty stations list to GCS."""
        storage = GCSStorage(bucket_name="test-bucket")
        result = storage.store_stations([])
        assert result == "gs://test-bucket/"

    @patch("storage.gcs.GCS_AVAILABLE", True)
    @patch("storage.gcs.storage")
    @patch("storage.gcs.LocalStorage")
    def test_store_stations_retry_logic(self, mock_local_storage, mock_storage):
        """Test retry logic for GCS upload failures."""
        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        # Mock local storage
        mock_local = Mock()
        mock_local.store_stations.return_value = "/tmp/stations_20240101_120000.parquet"
        mock_local_storage.return_value = mock_local

        # Make upload fail twice, then succeed
        mock_blob.upload_from_filename.side_effect = [
            google_exceptions.ServiceUnavailable("First failure"),
            google_exceptions.ServiceUnavailable("Second failure"),
            None,  # Success on third attempt
        ]

        storage = GCSStorage(bucket_name="test-bucket")
        storage.local_storage = mock_local
        storage.bucket = mock_bucket

        result = storage.store_stations(SAMPLE_STATIONS)

        # Should have retried 3 times total
        assert mock_blob.upload_from_filename.call_count == 3
        assert "gs://" in result


class TestDataLoader:
    """Test data loader integration."""

    @patch.object(CityBikesExtractor, "extract_all_stations")
    def test_data_loader_initialization(self, mock_extract):
        """Test DataLoader initialization."""
        mock_extractor = Mock()
        mock_storage = Mock()
        loader = DataLoader(extractor=mock_extractor, storage=mock_storage)
        assert loader.extractor is mock_extractor
        assert loader.storage is mock_storage

    @patch.object(CityBikesExtractor, "extract_all_stations")
    def test_load_all_stations_success(self, mock_extract):
        """Test successful extraction and storage."""
        mock_extractor = CityBikesExtractor()
        mock_storage = Mock()
        mock_storage.store_stations.return_value = "/path/to/data.parquet"

        mock_extract.return_value = SAMPLE_STATIONS

        loader = DataLoader(extractor=mock_extractor, storage=mock_storage)
        stations, storage_path = loader.load_all_stations()

        assert stations == SAMPLE_STATIONS
        assert storage_path == "/path/to/data.parquet"
        mock_extract.assert_called_once()
        mock_storage.store_stations.assert_called_once_with(SAMPLE_STATIONS)

    @patch.object(CityBikesExtractor, "extract_all_stations")
    def test_load_all_stations_empty(self, mock_extract):
        """Test extraction with no stations."""
        mock_extractor = CityBikesExtractor()
        mock_storage = Mock()
        mock_extract.return_value = []

        loader = DataLoader(extractor=mock_extractor, storage=mock_storage)
        stations, storage_path = loader.load_all_stations()

        assert stations == []
        assert storage_path == ""
        mock_storage.store_stations.assert_not_called()

    @patch.object(CityBikesExtractor, "extract_all_stations")
    def test_load_all_stations_storage_error(self, mock_extract):
        """Test storage error propagation."""
        mock_extractor = CityBikesExtractor()
        mock_storage = Mock()
        mock_extract.return_value = SAMPLE_STATIONS
        mock_storage.store_stations.side_effect = StorageError("Test storage error")

        loader = DataLoader(extractor=mock_extractor, storage=mock_storage)

        with pytest.raises(StorageError):
            loader.load_all_stations()