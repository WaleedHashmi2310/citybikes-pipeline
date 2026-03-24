"""Abstract storage interface for CityBikes pipeline."""

import logging
from abc import ABC, abstractmethod
from typing import List
from ingestion.schemas import NormalizedStation

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage layer errors."""

    pass


class StorageInterface(ABC):
    """Abstract base class for storage implementations.

    Defines the interface for storing normalized station data to various
    backends (local filesystem, Google Cloud Storage, etc.).
    """

    @abstractmethod
    def store_stations(self, stations: List[NormalizedStation]) -> str:
        """Store normalized stations to storage backend.

        Args:
            stations: List of normalized station records

        Returns:
            Storage path/URI where data was written

        Raises:
            StorageError: If storage operation fails
        """
        pass
