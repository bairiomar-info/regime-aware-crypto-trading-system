"""Risk decisions and immutable portfolio exposure limits."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class RiskDecision(StrEnum):
    ALLOW = "ALLOW"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True)
class RiskLimits:
    max_position_weight: Decimal = Decimal("1")
    max_portfolio_exposure: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        for name, value in (("max_position_weight", self.max_position_weight), ("max_portfolio_exposure", self.max_portfolio_exposure)):
            if not value.is_finite() or not Decimal("0") < value <= Decimal("1"):
                raise ValueError(f"{name} must be within (0, 1]")


@dataclass(frozen=True)
class RiskCheck:
    decision: RiskDecision
    reason: str

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("reason must not be empty")
