"""Canonical OHLCV candle model."""

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .instrument import Instrument
from .timeframe import Timeframe


class Candle(BaseModel):
    """Validated, exchange-independent market candle."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    instrument: Instrument
    timeframe: Timeframe
    open_time: datetime
    close_time: datetime
    open: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0)
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: Decimal = Field(ge=0)
    quote_volume: Decimal = Field(ge=0)
    trade_count: int = Field(ge=0)
    taker_buy_base_volume: Decimal = Field(ge=0)
    taker_buy_quote_volume: Decimal = Field(ge=0)
    source: str = Field(min_length=1)
    is_closed: bool

    @model_validator(mode="after")
    def validate_structure(self) -> "Candle":
        if self.open_time.tzinfo is None or self.open_time.utcoffset() is None:
            raise ValueError("open_time must be timezone-aware")
        if self.close_time.tzinfo is None or self.close_time.utcoffset() is None:
            raise ValueError("close_time must be timezone-aware")
        if self.open_time.tzinfo != timezone.utc or self.close_time.tzinfo != timezone.utc:
            raise ValueError("open_time and close_time must use UTC")
        if self.close_time <= self.open_time:
            raise ValueError("close_time must be after open_time")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be at least open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be at most open, close, and high")
        return self
