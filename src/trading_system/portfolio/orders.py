"""Pure conversion of portfolio rebalances into spot order intents."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: OrderSide
    notional: Decimal
    reason: str

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        if not self.notional.is_finite() or self.notional <= 0:
            raise ValueError("notional must be positive and finite")
        if not self.reason:
            raise ValueError("reason must not be empty")


def order_intents(delta_weights: tuple[tuple[str, Decimal], ...], equity: Decimal) -> tuple[OrderIntent, ...]:
    if not equity.is_finite() or equity <= 0:
        raise ValueError("equity must be positive and finite")
    result: list[OrderIntent] = []
    for symbol, delta in delta_weights:
        if not delta.is_finite():
            raise ValueError("delta weights must be finite")
        if delta > 0:
            result.append(OrderIntent(symbol, OrderSide.BUY, delta * equity, "rebalance_increase"))
        elif delta < 0:
            result.append(OrderIntent(symbol, OrderSide.SELL, -delta * equity, "rebalance_decrease"))
    return tuple(result)
