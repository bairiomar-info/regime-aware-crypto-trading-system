"""Versioned asset lineage events."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LineageEventType(StrEnum):
    """Supported economic-asset lineage events."""

    RENAME = "rename"
    REBRAND = "rebrand"
    MIGRATION = "migration"
    CHAIN_MIGRATION = "chain_migration"
    REDENOMINATION = "redenomination"
    REISSUE = "reissue"
    REDEPLOYMENT = "redeployment"
    SYMBOL_CHANGE = "symbol_change"
    EXCHANGE_LISTING = "exchange_listing"
    EXCHANGE_DELISTING = "exchange_delisting"


class LineageConfidence(StrEnum):
    """Confidence assigned to lineage evidence."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CONFLICTED = "conflicted"


class AssetLineageEvent(BaseModel):
    """Immutable, evidence-backed relationship between asset identities."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(min_length=1)
    event_type: LineageEventType
    effective_time: datetime
    predecessor_asset_id: str | None = Field(default=None, min_length=1)
    successor_asset_id: str | None = Field(default=None, min_length=1)
    conversion_ratio: Decimal | None = Field(default=None, gt=0)
    continuous_history: bool | None = None
    source: str = Field(min_length=1)
    source_timestamp: datetime | None = None
    confidence: LineageConfidence
    notes: str | None = None

    @field_validator("effective_time", "source_timestamp")
    @classmethod
    def require_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("timestamps must be timezone-aware")
        if value is not None and value.tzinfo != timezone.utc:
            raise ValueError("timestamps must use UTC")
        return value

    @field_validator("event_id", "predecessor_asset_id", "successor_asset_id")
    @classmethod
    def normalize_identifiers(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @model_validator(mode="after")
    def validate_lineage(self) -> "AssetLineageEvent":
        if self.predecessor_asset_id is None and self.successor_asset_id is None:
            raise ValueError("at least one predecessor or successor asset is required")
        if self.predecessor_asset_id == self.successor_asset_id:
            raise ValueError("predecessor and successor must differ")
        return self
