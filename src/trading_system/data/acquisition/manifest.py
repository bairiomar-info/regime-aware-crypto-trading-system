"""Reproducible acquisition manifest models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AcquisitionManifest(BaseModel):
    """Immutable record describing one acquisition result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_name: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    requested_start: datetime
    requested_end: datetime
    persisted_start: datetime | None = None
    persisted_end: datetime | None = None
    candle_count: int = Field(ge=0)
    status: Literal["complete", "partial", "failed"]
    duplicate_count: int = Field(default=0, ge=0)
    gap_count: int = Field(default=0, ge=0)
    validation_version: str = Field(min_length=1)

    @field_validator("requested_start", "requested_end", "persisted_start", "persisted_end")
    @classmethod
    def require_aware_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("manifest timestamps must be timezone-aware")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_ranges(self) -> "AcquisitionManifest":
        if self.requested_end <= self.requested_start:
            raise ValueError("requested_end must be after requested_start")
        if self.persisted_start is not None and self.persisted_end is not None:
            if self.persisted_end < self.persisted_start:
                raise ValueError("persisted_end must not precede persisted_start")
        if self.status == "complete" and self.candle_count == 0:
            raise ValueError("complete acquisition cannot contain zero candles")
        return self
