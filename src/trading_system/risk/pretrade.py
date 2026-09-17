"""Fail-closed pre-trade authorization for spot order intents."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_system.compliance.classification import AssetCompliance, validate_asset_compliance
from trading_system.compliance.gate import ComplianceDecision, evaluate_symbol
from trading_system.portfolio.orders import OrderIntent, OrderSide

from .checks import check_target_weight
from .models import RiskDecision, RiskLimits


@dataclass(frozen=True)
class PreTradeResult:
    allowed: bool
    reason: str


def authorize_order(
    order: OrderIntent,
    *,
    asset: AssetCompliance,
    target_weight: Decimal,
    current_exposure: Decimal,
    limits: RiskLimits,
    forbidden_symbols: frozenset[str] = frozenset(),
) -> PreTradeResult:
    """Authorize one order only when every hard compliance and risk gate passes."""
    compliance = evaluate_symbol(order.symbol, forbidden_symbols)
    if compliance.decision is ComplianceDecision.REJECT:
        return PreTradeResult(False, compliance.reason)
    if asset.symbol != order.symbol:
        return PreTradeResult(False, "asset_symbol_mismatch")
    try:
        validate_asset_compliance(asset)
    except ValueError as exc:
        return PreTradeResult(False, str(exc))
    if order.side not in (OrderSide.BUY, OrderSide.SELL):
        return PreTradeResult(False, "unsupported_order_side")
    risk = check_target_weight(target_weight, current_exposure, limits)
    if risk.decision is not RiskDecision.ALLOW:
        return PreTradeResult(False, risk.reason)
    return PreTradeResult(True, "authorized")
