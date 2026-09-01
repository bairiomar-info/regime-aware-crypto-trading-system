"""Pure models for resumable historical-data acquisition."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from ..models import Instrument, Timeframe


class AcquisitionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class AcquisitionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str = Field(min_length=1)
    instrument: Instrument
    timeframe: Timeframe
    start: datetime
    end: datetime

    def model_post_init(self, __context: object) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("acquisition bounds must be timezone-aware")
        if self.end <= self.start:
            raise ValueError("acquisition end must be after start")


class AcquisitionChunk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    start: datetime
    end: datetime
    sequence: int = Field(ge=0)

    def model_post_init(self, __context: object) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("chunk bounds must be timezone-aware")
        if self.end <= self.start:
            raise ValueError("chunk end must be after start")


class AcquisitionCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request: AcquisitionRequest
    last_successful_boundary: datetime | None = None
    status: AcquisitionStatus = AcquisitionStatus.PENDING

    def model_post_init(self, __context: object) -> None:
        if self.last_successful_boundary is not None:
            if self.last_successful_boundary.tzinfo is None:
                raise ValueError("checkpoint boundary must be timezone-aware")
            if not (self.request.start <= self.last_successful_boundary <= self.request.end):
                raise ValueError("checkpoint boundary must fall within acquisition bounds")


class AcquisitionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk: AcquisitionChunk
    records_received: int = Field(ge=0)
    raw_persisted: bool
    validation_passed: bool

