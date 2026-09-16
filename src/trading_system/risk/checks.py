"""Pure portfolio risk checks."""

from __future__ import annotations

from decimal import Decimal

from .models import RiskCheck, RiskDecision, RiskLimits


def check_target_weight(target_weight: Decimal, current_exposure: Decimal, limits: RiskLimits) -> RiskCheck:
    if not target_weight.is_finite() or target_weight < 0:
        return RiskCheck(RiskDecision.NO_TRADE, "invalid_target_weight")
    if not current_exposure.is_finite() or current_exposure < 0:
        return RiskCheck(RiskDecision.NO_TRADE, "invalid_current_exposure")
    if target_weight > limits.max_position_weight:
        return RiskCheck(RiskDecision.NO_TRADE, "position_weight_limit")
    if target_weight + current_exposure > limits.max_portfolio_exposure:
        return RiskCheck(RiskDecision.NO_TRADE, "portfolio_exposure_limit")
    return RiskCheck(RiskDecision.ALLOW, "within_limits")
