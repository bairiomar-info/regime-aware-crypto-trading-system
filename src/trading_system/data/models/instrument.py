"""Canonical instrument model."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MarketType(StrEnum):
    """Supported market types."""

    SPOT = "spot"


class Instrument(BaseModel):
    """Exchange-independent description of a tradable spot instrument."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(min_length=1)
    base_asset: str = Field(min_length=1)
    quote_asset: str = Field(min_length=1)
    market_type: MarketType = MarketType.SPOT
    exchange: str = Field(min_length=1)

    @field_validator("symbol", "base_asset", "quote_asset", "exchange")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        return value.upper()
