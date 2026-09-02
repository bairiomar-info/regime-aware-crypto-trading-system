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
        (TrendState.UP, TrendState.NEUTRAL): Transition.NEUTRAL_TO_UP,
        (TrendState.UP, TrendState.DOWN): Transition.DOWN_TO_UP,
        (TrendState.NEUTRAL, TrendState.UP): Transition.UP_TO_NEUTRAL,
        (TrendState.NEUTRAL, TrendState.DOWN): Transition.DOWN_TO_NEUTRAL,
        (TrendState.DOWN, TrendState.UP): Transition.UP_TO_DOWN,
        (TrendState.DOWN, TrendState.NEUTRAL): Transition.NEUTRAL_TO_DOWN,
    }
    return pairs[(previous, current)]


def evidence_confidence(states: Iterable[object | None]) -> Decimal:
    """Return the fraction of present dimensions agreeing with the majority.

    This is evidence coherence, not a predictive probability. Missing
    dimensions are excluded from both numerator and denominator.
    """
    present = [state for state in states if state is not None]
    if not present:
        return Decimal("0")
    counts: dict[object, int] = {}
    for state in present:
        counts[state] = counts.get(state, 0) + 1
    return Decimal(max(counts.values())) / Decimal(len(present))
