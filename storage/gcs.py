"""Google Cloud Storage implementation."""

import logging
import tempfile
import itertools
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from ingestion.schemas import NormalizedStation
from storage.interface import StorageInterface, StorageError
from storage.local import LocalStorage  # Reuse local storage for Parquet writing

if TYPE_CHECKING:
    from google.cloud import storage as gcs_module
    from google.api_core import exceptions as google_exceptions_module

logger = logging.getLogger(__name__)

try:
    from google.cloud import storage
    from google.api_core import exceptions as google_exceptions

    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

    # Create a dummy exception class to avoid NameError in decorator
    class DummyGoogleException(Exception):
        pass

    class DummyGoogleExceptionsModule:
        ServiceUnavailable = DummyGoogleException

    google_exceptions = DummyGoogleExceptionsModule()
    storage = None  # type: ignore[assignment]
    logger.warning(
        "google-cloud-storage not installed. GCSStorage will not work. "
        "Install with: pip install google-cloud-storage"
    )


class GCSStorage(StorageInterface):
    """Store station data to Google Cloud Storage bucket.

    Writes Parquet files locally first, then uploads to GCS with retry logic.
    Maintains same partition structure as LocalStorage (date-first: date={date}/city={city}).

    Args:
        bucket_name: GCS bucket name
        credentials_path: Optional path to service account JSON file
            (default: uses GOOGLE_APPLICATION_CREDENTIALS env var)
        project_id: Optional Google Cloud project ID
    """

    if TYPE_CHECKING:
        # Type hints for IDE/linter when google-cloud-storage is not installed
        from storage.local import LocalStorage

        client: "gcs_module.Client"
        bucket: "gcs_module.Bucket"
        local_storage: LocalStorage

    def __init__(
        self,
        bucket_name: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        if not GCS_AVAILABLE:
            raise ImportError(
                "google-cloud-storage not installed. "
                "Install with: pip install google-cloud-storage"
            )

        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self.project_id = project_id

        # Initialize GCS client
        self._init_gcs_client()

        # Use LocalStorage for temporary Parquet file creation
        self.local_storage = LocalStorage(base_path=tempfile.gettempdir())

        logger.debug(
            f"Initialized GCSStorage for bucket: {bucket_name}, "
            f"project: {project_id or 'default'}"
        )

    def _init_gcs_client(self):
        """Initialize Google Cloud Storage client."""
        assert storage is not None, "GCS storage module not available"

        try:
            if self.credentials_path:
                self.client = storage.Client.from_service_account_json(  # type: ignore[attr-defined]
                    self.credentials_path, project=self.project_id
                )
            else:
                self.client = storage.Client(project=self.project_id)  # type: ignore[attr-defined]
            self.bucket = self.client.bucket(self.bucket_name)
            logger.debug(f"GCS client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise StorageError(f"GCS client initialization failed: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(google_exceptions.ServiceUnavailable),  # type: ignore[attr-defined]
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _upload_to_gcs(self, local_path: Path, gcs_path: str):
        """Upload file to GCS with retry logic.

        Args:
            local_path: Path to local file
            gcs_path: Destination path in GCS bucket

        Raises:
            StorageError: If upload fails after retries
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(str(local_path))
            logger.debug(f"Uploaded {local_path} to gs://{self.bucket_name}/{gcs_path}")
        except Exception as e:
            logger.error(f"GCS upload failed for {local_path}: {e}")
            raise

    def store_stations(self, stations: List[NormalizedStation]) -> str:
        """Store normalized stations to GCS bucket.

        Args:
            stations: List of normalized station records

        Returns:
            GCS URI where data was written (gs://bucket/path) - first city's URI

        Raises:
            StorageError: If storage operation fails
        """
        if not stations:
            logger.warning("Empty stations list provided, nothing to store")
            return f"gs://{self.bucket_name}/"

        try:
            # Sort stations by city for grouping
            stations_sorted = sorted(stations, key=lambda s: s.city)
            # Create list of city groups before iterating (to know count)
            groups = [(city, list(city_stations)) for city, city_stations in itertools.groupby(stations_sorted, key=lambda s: s.city)]
            first_gcs_uri = None

            # Process each city group
            for city, city_stations_list in groups:
                # Write Parquet file locally for this city using LocalStorage
                local_path = Path(self.local_storage.store_stations(city_stations_list))

                # Determine GCS destination path (maintain partition structure)
                batch_timestamp = city_stations_list[0].ingestion_timestamp
                batch_date = batch_timestamp.date()
                filename = local_path.name

                # GCS path: raw/date=YYYY-MM-DD/city=CityName/filename
                gcs_path = f"raw/date={batch_date}/city={city}/{filename}"

                # Upload to GCS with retry logic
                logger.info(
                    f"Uploading {len(city_stations_list)} stations to GCS for city {city}: "
                    f"gs://{self.bucket_name}/{gcs_path}"
                )
                self._upload_to_gcs(local_path, gcs_path)

                # Clean up local temporary file
                try:
                    local_path.unlink()
                    logger.debug(f"Cleaned up temporary file: {local_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {local_path}: {e}")

                gcs_uri = f"gs://{self.bucket_name}/{gcs_path}"
                if first_gcs_uri is None:
                    first_gcs_uri = gcs_uri

            logger.info(f"Successfully stored stations for {len(groups)} cities")
            # first_gcs_uri is guaranteed to be set because groups is non-empty (stations non-empty)
            assert first_gcs_uri is not None, "No cities processed despite non-empty stations list"
            return first_gcs_uri

        except Exception as e:
            logger.error(f"Failed to store stations to GCS: {e}")
            raise StorageError(f"GCS storage failed: {e}") from e
