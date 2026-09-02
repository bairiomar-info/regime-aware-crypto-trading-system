"""Typed contracts for the V1 multidimensional market-regime layer."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrendState(str, Enum):
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"
    UP = "UP"


class LevelState(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class Transition(str, Enum):
    PERSISTING_UP = "PERSISTING_UP"
    PERSISTING_NEUTRAL = "PERSISTING_NEUTRAL"
    PERSISTING_DOWN = "PERSISTING_DOWN"
    UP_TO_NEUTRAL = "UP_TO_NEUTRAL"
    UP_TO_DOWN = "UP_TO_DOWN"
    NEUTRAL_TO_UP = "NEUTRAL_TO_UP"
    NEUTRAL_TO_DOWN = "NEUTRAL_TO_DOWN"
    DOWN_TO_NEUTRAL = "DOWN_TO_NEUTRAL"
    DOWN_TO_UP = "DOWN_TO_UP"


class MarketState(BaseModel):
    """Immutable point-in-time market state; it contains no trading decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    decision_time: datetime
    trend: TrendState
    volatility: LevelState
    breadth: LevelState
    dispersion: LevelState
    correlation: LevelState
    transition: Transition
    state_age: int = Field(ge=1)
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))

    @field_validator("decision_time")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("decision_time must be timezone-aware UTC")
        return value

    @field_validator("confidence", mode="before")
    @classmethod
    def parse_confidence(cls, value: Decimal | str) -> Decimal:
        return Decimal(str(value))
