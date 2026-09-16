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
        if not isinstance(self.symbol, str) or not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase identifier")
        if not isinstance(self.notional, Decimal) or not self.notional.is_finite() or self.notional <= 0:
            raise ValueError("notional must be a positive finite Decimal")
        if not isinstance(self.side, OrderSide):
            raise TypeError("side must be an OrderSide")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")


def order_intents(delta_weights: tuple[tuple[str, Decimal], ...], equity: Decimal) -> tuple[OrderIntent, ...]:
    """Convert signed target deltas into non-zero BUY/SELL spot intents."""
    if not isinstance(equity, Decimal) or not equity.is_finite() or equity <= 0:
        raise ValueError("equity must be a positive finite Decimal")
    result: list[OrderIntent] = []
    seen: set[str] = set()
    for symbol, delta in delta_weights:
        if not isinstance(symbol, str) or not symbol or symbol != symbol.upper():
            raise ValueError("symbols must be non-empty uppercase identifiers")
        if symbol in seen:
            raise ValueError("symbols must be unique")
        seen.add(symbol)
        if not isinstance(delta, Decimal) or not delta.is_finite():
            raise ValueError("delta weights must be finite Decimals")
        if delta > 0:
            result.append(OrderIntent(symbol, OrderSide.BUY, delta * equity, "rebalance_increase"))
        elif delta < 0:
            result.append(OrderIntent(symbol, OrderSide.SELL, -delta * equity, "rebalance_decrease"))
    return tuple(result)
