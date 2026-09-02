"""Contracts for deterministic raw-to-canonical transformation."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class QualityClassification(StrEnum):
    """Classification of an interval/observation after canonicalization."""

    VALID = "valid"
    NO_TRADES = "no_trades"
    DATA_GAP = "data_gap"
    SOURCE_FAILURE = "source_failure"
    HALT = "halt"
    BREAK = "break"
    UNKNOWN_GAP = "unknown_gap"
    DUPLICATE = "duplicate"
    DATA_CONFLICT = "data_conflict"


class CanonicalizationContract(BaseModel):
    """Immutable versioned contract governing raw-to-canonical transformation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    normalization_version: str = Field(min_length=1)
    validation_version: str = Field(min_length=1)
    require_closed_candles: bool = True
    numeric_representation: str = Field(default="decimal128", min_length=1)
    timestamp_timezone: str = Field(default="UTC", min_length=1)
    fabricate_missing_candles: bool = False
    reject_conflicting_duplicates: bool = True

    @field_validator("timestamp_timezone")
    @classmethod
    def require_utc(cls, value: str) -> str:
        if value.upper() != "UTC":
            raise ValueError("canonical timestamps must use UTC")
        return "UTC"

    @model_validator(mode="after")
    def validate_invariants(self) -> "CanonicalizationContract":
        if self.fabricate_missing_candles:
            raise ValueError("canonicalization must not fabricate missing candles")
        if self.numeric_representation.lower() != "decimal128":
            raise ValueError("V1 canonical numeric representation must be decimal128")
        return self


class QualityDiagnostic(BaseModel):
    """Immutable diagnostic explaining a canonical data-quality classification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    classification: QualityClassification
    observed_at: datetime
    message: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)

    @field_validator("observed_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("observed_at must be UTC-aware")
        return value
