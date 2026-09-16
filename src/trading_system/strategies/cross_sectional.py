"""Causal cross-sectional momentum research strategy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.research.time import require_utc

from .models import SignalDirection, StrategySignal


@dataclass(frozen=True)
class CrossSectionalObservation:
    """One asset's point-in-time trailing return."""

    symbol: str
    decision_time: datetime
    trailing_return: Decimal

    def __post_init__(self) -> None:
        require_utc(self.decision_time, name="decision_time")
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        if not self.trailing_return.is_finite():
            raise ValueError("trailing_return must be finite")


@dataclass(frozen=True)
class CrossSectionalMomentumConfig:
    """Configuration for selecting the strongest point-in-time assets."""

    top_n: int
    target_weight: Decimal
    min_return: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.top_n <= 0:
            raise ValueError("top_n must be positive")
        if not self.target_weight.is_finite() or not Decimal("0") < self.target_weight <= Decimal("1"):
            raise ValueError("target_weight must be within (0, 1]")
        if not self.min_return.is_finite():
            raise ValueError("min_return must be finite")


class CrossSectionalMomentum:
    """Select the strongest eligible assets using only same-time observations."""

    name = "cross_sectional_momentum"

    def __init__(self, config: CrossSectionalMomentumConfig) -> None:
        self.config = config

    def generate_signals(self, observations: tuple[CrossSectionalObservation, ...]) -> tuple[StrategySignal, ...]:
        if not observations:
            return ()
        decision_time = observations[0].decision_time
        if any(item.decision_time != decision_time for item in observations):
            raise ValueError("all cross-sectional observations must share decision_time")

        unique_symbols: set[str] = set()
        for item in observations:
            if item.symbol in unique_symbols:
                raise ValueError("duplicate symbols are not allowed")
            unique_symbols.add(item.symbol)

        eligible = [item for item in observations if item.trailing_return > self.config.min_return]
        ranked = sorted(eligible, key=lambda item: (-item.trailing_return, item.symbol))
        selected = {item.symbol for item in ranked[: self.config.top_n]}

        return tuple(
            StrategySignal(
                decision_time=decision_time,
                symbol=item.symbol,
                direction=SignalDirection.LONG,
                reason="cross_sectional_momentum_selected",
                score=item.trailing_return,
                target_weight=self.config.target_weight,
                metadata=(("rank", str(rank)),),
            )
            for rank, item in enumerate(ranked[: self.config.top_n], start=1)
            if item.symbol in selected
        )
