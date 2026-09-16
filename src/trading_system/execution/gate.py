"""Mandatory pre-trade gate combining compliance and risk checks."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_system.compliance.spot import SpotComplianceConfig, validate_spot_symbol
from trading_system.portfolio.orders import OrderIntent
from trading_system.portfolio.state import PortfolioState
from trading_system.risk.limits import RiskLimits, validate_order_risk


@dataclass(frozen=True)
class PreTradeConfig:
    risk: RiskLimits = RiskLimits()
    spot: SpotComplianceConfig = SpotComplianceConfig()


def validate_pre_trade(
    state: PortfolioState,
    order: OrderIntent,
    price: Decimal,
    config: PreTradeConfig = PreTradeConfig(),
    *,
    prices: dict[str, Decimal] | None = None,
) -> None:
    """Raise unless an order satisfies hard spot-compliance and risk controls."""
    validate_spot_symbol(order.symbol, config.spot)
    validate_order_risk(state, order, price, config.risk, prices=prices)
