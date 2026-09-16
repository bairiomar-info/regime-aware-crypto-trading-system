"""Mandatory pre-trade gate combining asset compliance and risk checks."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_system.compliance.classification import AssetCompliance, validate_asset_compliance
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
    asset_compliance: AssetCompliance | None = None,
) -> None:
    """Raise unless an order has explicit hard compliance evidence and passes risk."""
    validate_spot_symbol(order.symbol, config.spot)
    if asset_compliance is None:
        raise ValueError("explicit asset compliance evidence is required")
    if asset_compliance.symbol != order.symbol:
        raise ValueError("asset compliance symbol must match order symbol")
    validate_asset_compliance(asset_compliance)
    validate_order_risk(state, order, price, config.risk, prices=prices)
