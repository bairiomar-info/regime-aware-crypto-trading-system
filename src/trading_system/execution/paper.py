"""Deterministic paper-trading execution adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.compliance.classification import AssetCompliance
from trading_system.portfolio.orders import OrderIntent
from trading_system.portfolio.state import PortfolioState
from trading_system.research.time import require_utc

from .gate import PreTradeConfig
from .service import execute_order


@dataclass(frozen=True)
class PaperFill:
    timestamp: datetime
    order: OrderIntent
    fill_price: Decimal
    fee_rate: Decimal

    def __post_init__(self) -> None:
        require_utc(self.timestamp, name="paper fill timestamp")
        if not isinstance(self.fill_price, Decimal) or not self.fill_price.is_finite() or self.fill_price <= 0:
            raise ValueError("fill_price must be a positive finite Decimal")
        if not isinstance(self.fee_rate, Decimal) or not self.fee_rate.is_finite() or self.fee_rate < 0 or self.fee_rate >= 1:
            raise ValueError("fee_rate must be a finite Decimal in [0, 1)")


@dataclass(frozen=True)
class PaperExecutionResult:
    state: PortfolioState
    fill: PaperFill


def execute_paper_order(
    state: PortfolioState,
    order: OrderIntent,
    *,
    timestamp: datetime,
    market_price: Decimal,
    fill_price: Decimal,
    fee_rate: Decimal,
    config: PreTradeConfig = PreTradeConfig(),
    prices: dict[str, Decimal] | None = None,
    asset_compliance: AssetCompliance | None = None,
) -> PaperExecutionResult:
    """Run one paper fill through the same mandatory pre-trade gate as execution."""
    require_utc(timestamp, name="paper fill timestamp")
    new_state = execute_order(
        state,
        order,
        market_price=market_price,
        fill_price=fill_price,
        fee_rate=fee_rate,
        config=config,
        prices=prices,
        asset_compliance=asset_compliance,
    )
    return PaperExecutionResult(new_state, PaperFill(timestamp, order, fill_price, fee_rate))
