"""Immutable research-only strategy inputs and signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from trading_system.features.models import FeatureSnapshot
from trading_system.regime.models import MarketState
from trading_system.research.time import require_utc


class SignalDirection(StrEnum):
    """Directions permitted by the long-only spot research architecture."""

    LONG = "LONG"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True)
class PortfolioContext:
    """Minimal immutable portfolio context available to research strategies.

    It deliberately contains no order, fill, or exchange state. Portfolio and
    risk layers remain responsible for converting a research signal into an
    allocation or executable plan.
    """

    as_of: datetime
    cash: Decimal
    current_weight: Decimal

    def __post_init__(self) -> None:
        require_utc(self.as_of, name="portfolio as_of")
        _finite_decimal(self.cash, name="cash")
        _finite_decimal(self.current_weight, name="current_weight")
        if self.cash < 0:
            raise ValueError("cash must be non-negative")
        if not Decimal("0") <= self.current_weight <= Decimal("1"):
            raise ValueError("current_weight must be within [0, 1]")


@dataclass(frozen=True)
class StrategyContext:
    """Point-in-time information supplied to a research strategy."""

    decision_time: datetime
    symbol: str
    features: FeatureSnapshot
    regime: MarketState | None = None
    portfolio: PortfolioContext | None = None

    def __post_init__(self) -> None:
        require_utc(self.decision_time, name="decision_time")
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        if self.features.decision_time != self.decision_time:
            raise ValueError("features must match decision_time")
        if self.regime is not None and self.regime.decision_time != self.decision_time:
            raise ValueError("regime must match decision_time")
        if self.portfolio is not None and self.portfolio.as_of > self.decision_time:
            raise ValueError("portfolio context cannot be from the future")


@dataclass(frozen=True)
class StrategySignal:
    """A research decision, not an order or an executable allocation."""

    decision_time: datetime
    symbol: str
    direction: SignalDirection
    reason: str
    score: Decimal | None = None
    confidence: Decimal | None = None
    target_weight: Decimal | None = None
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        require_utc(self.decision_time, name="decision_time")
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        if not self.reason:
            raise ValueError("reason must not be empty")
        if self.score is not None:
            _finite_decimal(self.score, name="score")
        if self.confidence is not None:
            _finite_decimal(self.confidence, name="confidence")
            if not Decimal("0") <= self.confidence <= Decimal("1"):
                raise ValueError("confidence must be within [0, 1]")
        if self.direction is SignalDirection.LONG:
            if self.target_weight is None:
                raise ValueError("LONG signals require target_weight")
            _finite_decimal(self.target_weight, name="target_weight")
            if not Decimal("0") < self.target_weight <= Decimal("1"):
                raise ValueError("target_weight must be within (0, 1] for LONG signals")
        elif self.direction is SignalDirection.NO_TRADE:
            if self.target_weight is not None:
                raise ValueError("NO_TRADE signals must not set target_weight")
        else:
            raise ValueError("direction must be a supported SignalDirection")
        if not isinstance(self.metadata, tuple):
            raise TypeError("metadata must be an immutable tuple")
        keys: set[str] = set()
        for item in self.metadata:
            if not isinstance(item, tuple) or len(item) != 2 or not all(isinstance(value, str) for value in item):
                raise TypeError("metadata must contain string key/value pairs")
            if not item[0] or item[0] in keys:
                raise ValueError("metadata keys must be non-empty and unique")
            keys.add(item[0])


def _finite_decimal(value: Decimal, *, name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
