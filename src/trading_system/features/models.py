"""Validated feature outputs used by the regime research layer."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class FeatureSnapshot:
    """One causal market measurement at a finalized decision time."""

    decision_time: datetime
    trend_score: Decimal | None
    realized_volatility: Decimal | None
    breadth: Decimal | None
    cross_sectional_dispersion: Decimal | None
    average_pairwise_correlation: Decimal | None
    asset_count: int

    def __post_init__(self) -> None:
        if self.decision_time.tzinfo is None or self.decision_time.utcoffset() != timezone.utc.utcoffset(self.decision_time):
            raise ValueError("decision_time must be timezone-aware UTC")
        if self.asset_count < 0:
            raise ValueError("asset_count must be non-negative")
        for name in (
            "trend_score",
            "realized_volatility",
            "breadth",
            "cross_sectional_dispersion",
            "average_pairwise_correlation",
        ):
            value = getattr(self, name)
            if value is not None and not value.is_finite():
                raise ValueError(f"{name} must be finite")
        if self.realized_volatility is not None and self.realized_volatility < 0:
            raise ValueError("realized_volatility must be non-negative")
        for name in ("breadth", "average_pairwise_correlation"):
            value = getattr(self, name)
            if value is not None and not Decimal("-1") <= value <= Decimal("1"):
                raise ValueError(f"{name} must be within [-1, 1]")
        if self.breadth is not None and not Decimal("0") <= self.breadth <= Decimal("1"):
            raise ValueError("breadth must be within [0, 1]")
        if self.cross_sectional_dispersion is not None and self.cross_sectional_dispersion < 0:
            raise ValueError("cross_sectional_dispersion must be non-negative")
