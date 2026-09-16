"""Deterministic paper-trading execution adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.portfolio.orders import OrderIntent
from trading_system.portfolio.state import PortfolioState
from trading_system.compliance.classification import AssetCompliance

from .service import execute_order
from .gate import PreTradeConfig


@dataclass(frozen=True)
class PaperFill:
    timestamp: datetime
    order: OrderIntent
    fill_price: Decimal
    fee_rate: Decimal


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
    return PaperExecutionResult(
        state=new_state,
        fill=PaperFill(timestamp, order, fill_price, fee_rate),
    )
