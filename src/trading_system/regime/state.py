"""Market-state transition and evidence-coherence helpers."""

from collections.abc import Iterable
from decimal import Decimal

from .models import Transition, TrendState


def transition_for(current: TrendState, previous: TrendState | None) -> Transition:
    """Map the trend state pair to the frozen transition vocabulary."""
    if previous is None or current is previous:
        return {
            TrendState.UP: Transition.PERSISTING_UP,
            TrendState.NEUTRAL: Transition.PERSISTING_NEUTRAL,
            TrendState.DOWN: Transition.PERSISTING_DOWN,
        }[current]
    pairs = {
        (TrendState.UP, TrendState.NEUTRAL): Transition.UP_TO_NEUTRAL,
        (TrendState.UP, TrendState.DOWN): Transition.UP_TO_DOWN,
        (TrendState.NEUTRAL, TrendState.UP): Transition.NEUTRAL_TO_UP,
        (TrendState.NEUTRAL, TrendState.DOWN): Transition.NEUTRAL_TO_DOWN,
        (TrendState.DOWN, TrendState.UP): Transition.DOWN_TO_UP,
        (TrendState.DOWN, TrendState.NEUTRAL): Transition.DOWN_TO_NEUTRAL,
    }
    return pairs[(current, previous)]


def evidence_confidence(evidence: Iterable[bool | None]) -> Decimal:
    """Return the fraction of present evidence items that agree.

    This intentionally accepts explicit agreement flags rather than mixing
    incomparable categorical dimensions such as volatility and trend. It is
    evidence coherence, not a predictive probability.
    """
    present = [item for item in evidence if item is not None]
    if not present:
        return Decimal("0")
    return Decimal(sum(present)) / Decimal(len(present))
