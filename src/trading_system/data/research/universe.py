"""Deterministic point-in-time universe eligibility evaluation."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import EligibilityDecision, EligibilityReason, MembershipStatus
from .policy import UniversePolicy


def evaluate_eligibility(
    *,
    instrument_id: str,
    decision_time: datetime,
    policy: UniversePolicy,
    membership_status: MembershipStatus,
    market_type: str,
    quote_asset: str,
    history_bars: int,
    quote_volume: Decimal | str | None = None,
    classification: str | None = None,
    evidence_available_at: datetime | None = None,
) -> EligibilityDecision:
    """Evaluate one instrument using only as-of information.

    Callers are responsible for supplying observations whose own availability
    timestamp is no later than ``decision_time``. The explicit availability
    check prevents an accidentally future-dated evidence bundle from being
    accepted by the research layer.
    """
    if evidence_available_at is not None and evidence_available_at > decision_time:
        return EligibilityDecision(
            instrument_id=instrument_id,
            decision_time=decision_time,
            eligible=False,
            reasons=(EligibilityReason.FUTURE_INFORMATION,),
            policy_id=policy.policy_id,
            policy_version=policy.version,
            evidence_available_at=evidence_available_at,
        )

    reasons: list[EligibilityReason] = []

    if membership_status == MembershipStatus.NOT_LISTED:
        reasons.append(EligibilityReason.NOT_LISTED)
    elif membership_status == MembershipStatus.DELISTED:
        reasons.append(EligibilityReason.DELISTED)
    elif membership_status in (MembershipStatus.HALTED, MembershipStatus.LISTED):
        reasons.append(EligibilityReason.NOT_TRADABLE)
    elif membership_status != MembershipStatus.TRADABLE:
        reasons.append(EligibilityReason.NOT_TRADABLE)

    if market_type.upper() not in policy.allowed_market_types:
        reasons.append(EligibilityReason.WRONG_MARKET_TYPE)

    if quote_asset.upper() not in policy.allowed_quote_assets:
        reasons.append(EligibilityReason.DISALLOWED_QUOTE_ASSET)

    if (
        classification is not None
        and classification.upper() in policy.excluded_classifications
    ):
        reasons.append(EligibilityReason.EXCLUDED_CLASSIFICATION)

    if history_bars < policy.minimum_history_bars:
        reasons.append(EligibilityReason.INSUFFICIENT_HISTORY)

    if policy.minimum_quote_volume is not None:
        if quote_volume is None:
            reasons.append(EligibilityReason.INSUFFICIENT_LIQUIDITY)
        else:
            try:
                if Decimal(str(quote_volume)) < Decimal(policy.minimum_quote_volume):
                    reasons.append(EligibilityReason.INSUFFICIENT_LIQUIDITY)
            except InvalidOperation as exc:
                raise ValueError("quote_volume must be a valid decimal value") from exc

    eligible = not reasons
    if eligible:
        reasons = [EligibilityReason.ELIGIBLE]

    return EligibilityDecision(
        instrument_id=instrument_id,
        decision_time=decision_time,
        eligible=eligible,
        reasons=tuple(reasons),
        policy_id=policy.policy_id,
        policy_version=policy.version,
        evidence_available_at=evidence_available_at,
    )
