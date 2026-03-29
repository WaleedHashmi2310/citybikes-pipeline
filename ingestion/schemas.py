"""Pydantic schemas for CityBikes API data."""

from datetime import datetime
from typing import Optional, List, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Location(BaseModel):
    """Location schema for network."""

    city: str
    country: str
    latitude: float
    longitude: float


class NetworkSummary(BaseModel):
    """Network summary from /v2/networks endpoint."""

    id: str
    name: str
    href: str
    company: Union[str, List[str]]
    location: Location
    gbfs_href: Optional[str] = None
    ebikes: Optional[bool] = None


class NetworkListResponse(BaseModel):
    """Response from /v2/networks endpoint."""

    networks: List[NetworkSummary]


class StationExtra(BaseModel):
    """Extra fields for station."""

    uid: Optional[str] = None
    renting: Optional[Union[int, str]] = None
    returning: Optional[Union[int, str]] = None
    last_updated: Optional[Union[int, str]] = None
    has_ebikes: Optional[bool] = None
    ebikes: Optional[Union[int, str]] = None
    payment: Optional[List[str]] = None
    payment_terminal: Optional[bool] = Field(None, alias="payment-terminal")
    slots: Optional[Union[int, str]] = None
    rental_uris: Optional[dict] = None

    model_config = ConfigDict(populate_by_name=True)


class Station(BaseModel):
    """Station schema from network details endpoint."""

    id: str
    name: str
    latitude: float
    longitude: float
    timestamp: str  # UTC timestamp string
    free_bikes: int
    empty_slots: Optional[int] = 0
    extra: Optional[StationExtra] = None

    @field_validator('empty_slots', mode='before')
    @classmethod
    def convert_none_to_zero(cls, v):
        """Convert None to 0 for empty_slots."""
        if v is None:
            return 0
        return v


class Vehicle(BaseModel):
    """Vehicle schema (for roaming vehicles)."""

    id: str
    latitude: float
    longitude: float
    timestamp: str
    extra: Optional[dict] = None
    kind: Optional[str] = None  # "bike", "ebike", "scooter"


class NetworkDetails(BaseModel):
    """Network details from /v2/networks/{network_id} endpoint."""

    id: str
    name: str
    href: str
    company: Union[str, List[str]]
    location: Location
    gbfs_href: Optional[str] = None
    ebikes: Optional[bool] = None
    stations: List[Station]
    vehicles: Optional[List[Vehicle]] = None


class NormalizedStation(BaseModel):
    """Normalized station record for storage."""

    station_id: str = Field(alias="id")
    name: str
    latitude: float
    longitude: float
    free_bikes: int
    empty_slots: int
    slots: Optional[int] = None  # Total capacity from extra.slots, or free_bikes + empty_slots
    timestamp: str  # Original station timestamp from API
    ingestion_timestamp: datetime  # When we ingested the data
    city: str  # City name from network location
    extra: Optional[Dict[str, Any]] = None  # Raw extra field as JSON

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
