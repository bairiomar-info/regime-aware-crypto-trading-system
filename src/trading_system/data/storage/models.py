"""Storage and reproducibility metadata models."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class ChecksumStatus(StrEnum):
    """Result of comparing a provider checksum with our calculated checksum."""

    VERIFIED = "verified"
    MISMATCH = "mismatch"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class RawArtifact(BaseModel):
    """Immutable identity of the exact bytes of a raw source artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    byte_size: int = Field(ge=0)
    media_type: str | None = None
    compression: str | None = None


class ArtifactAcquisition(BaseModel):
    """Immutable record of one attempt to obtain a raw artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    acquisition_id: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    source_locator: str = Field(min_length=1)
    retrieved_at: datetime
    filename: str | None = None
    provider_checksum: str | None = None
    checksum_status: ChecksumStatus = ChecksumStatus.UNAVAILABLE
    retrieval_status: str = Field(min_length=1)
    source_version: str | None = None
    etag: str | None = None
    last_modified: str | None = None

    @field_validator("retrieved_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("retrieved_at must be UTC-aware")
        return value


class AcquisitionRun(BaseModel):
    """Immutable execution-level provenance for one acquisition run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(min_length=1)
    started_at: datetime
    completed_at: datetime | None = None
    status: str = Field(min_length=1)
    code_commit: str | None = None
    configuration_hash: str | None = None
    artifact_acquisition_ids: tuple[str, ...] = ()

    @field_validator("started_at", "completed_at")
    @classmethod
    def require_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("acquisition run timestamps must be UTC-aware")
        return value

    @model_validator(mode="after")
    def validate_completion(self) -> "AcquisitionRun":
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        return self


class Provenance(BaseModel):
    """Legacy canonical-dataset provenance metadata; retained for compatibility."""

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


class CanonicalDatasetResource(BaseModel):
    """Immutable manifest entry for one canonical Parquet resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    byte_size: int = Field(ge=0)
    row_count: int = Field(ge=0)
    min_timestamp: datetime | None = None
    max_timestamp: datetime | None = None

    @field_validator("min_timestamp", "max_timestamp")
    @classmethod
    def require_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("resource timestamps must be UTC-aware")
        return value

    @model_validator(mode="after")
    def validate_timestamp_bounds(self) -> "CanonicalDatasetResource":
        if (
            self.min_timestamp is not None
            and self.max_timestamp is not None
            and self.max_timestamp < self.min_timestamp
        ):
            raise ValueError("max_timestamp must not precede min_timestamp")
        if self.row_count == 0 and (
            self.min_timestamp is not None or self.max_timestamp is not None
        ):
            raise ValueError("empty resources must not have timestamp bounds")
        return self


class CanonicalDatasetManifest(BaseModel):
    """Immutable manifest describing one canonical dataset release."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(
        pattern=r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
    )
    schema_version: str = Field(min_length=1)
    normalization_version: str = Field(min_length=1)
    validation_version: str = Field(min_length=1)
    input_artifact_ids: tuple[str, ...] = ()
    code_commit: str | None = None
    configuration_hash: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    resources: tuple[CanonicalDatasetResource, ...] = Field(min_length=1)
    total_row_count: int = Field(ge=0)
    min_timestamp: datetime | None = None
    max_timestamp: datetime | None = None

    @field_validator("min_timestamp", "max_timestamp")
    @classmethod
    def require_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("dataset timestamps must be UTC-aware")
        return value

    @model_validator(mode="after")
    def validate_manifest(self) -> "CanonicalDatasetManifest":
        calculated_rows = sum(resource.row_count for resource in self.resources)
        if calculated_rows != self.total_row_count:
            raise ValueError("total_row_count must equal the sum of resource row counts")

        resource_min = min(
            (resource.min_timestamp for resource in self.resources if resource.min_timestamp is not None),
            default=None,
        )
        resource_max = max(
            (resource.max_timestamp for resource in self.resources if resource.max_timestamp is not None),
            default=None,
        )
        if self.min_timestamp != resource_min:
            raise ValueError("min_timestamp must equal the earliest resource timestamp")
        if self.max_timestamp != resource_max:
            raise ValueError("max_timestamp must equal the latest resource timestamp")
        if self.min_timestamp is not None and self.max_timestamp is not None:
            if self.max_timestamp < self.min_timestamp:
                raise ValueError("max_timestamp must not precede min_timestamp")
        return self
