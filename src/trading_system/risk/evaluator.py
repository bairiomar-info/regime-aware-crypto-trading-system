"""Portfolio-aware risk evaluation."""

from __future__ import annotations

from decimal import Decimal

from .checks import check_target_weight
from .models import RiskCheck, RiskLimits


def evaluate_target(
    target_weight: Decimal,
    existing_exposure: Decimal,
    limits: RiskLimits,
) -> RiskCheck:
    """Return an explicit risk decision without mutating portfolio state."""
    return check_target_weight(target_weight, existing_exposure, limits)
