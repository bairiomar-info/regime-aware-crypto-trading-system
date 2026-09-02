"""Canonical economic asset identity and lifecycle models."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssetLifecycle(StrEnum):
    """Lifecycle state of the underlying economic asset."""

    UNKNOWN = "unknown"
    LISTED = "listed"
    ACTIVE = "active"
    HALTED = "halted"
    MIGRATED = "migrated"
    REISSUED = "reissued"
    DELISTED = "delisted"
    DEACTIVATED = "deactivated"


class Asset(BaseModel):
    """Stable internal identity for an economic asset."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    asset_id: str = Field(min_length=1)
    base_symbol: str = Field(min_length=1)
    lifecycle: AssetLifecycle = AssetLifecycle.UNKNOWN

    @field_validator("asset_id", "base_symbol")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        return value.upper()
