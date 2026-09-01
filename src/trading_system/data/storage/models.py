"""Storage and reproducibility metadata models."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StorageRecord(BaseModel):
    """Canonical identity for one immutable stored market-data record."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    provider: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    open_time: datetime

    @field_validator("provider", "symbol", "timeframe")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        return value.upper()

    @field_validator("open_time")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("open_time must be UTC-aware")
        return value


class Provenance(BaseModel):
    """Metadata required to reproduce a canonical dataset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    acquired_at: datetime
    normalization_version: str = Field(min_length=1)
    validation_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    source_request: str | None = None

    @field_validator("acquired_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("acquired_at must be UTC-aware")
        return value


class DatasetIdentity(BaseModel):
    """Stable logical identity for a research dataset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_name: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    start: datetime
    end: datetime
    provenance: Provenance

    @field_validator("start", "end")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("dataset bounds must be UTC-aware")
        return value

    def model_post_init(self, __context: object) -> None:
        if self.end <= self.start:
            raise ValueError("dataset end must be after start")
