"""Descriptive threshold-sensitivity diagnostics for the V1 regime classifier."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Sequence

from .classifier import DimensionConfig
from .models import MarketState, TrendState, Transition


@dataclass(frozen=True)
class SensitivityVariant:
    """A pre-registered perturbation of one dimension's quantile boundaries."""

    name: str
    lower_quantile: Decimal
    lower_exit_quantile: Decimal
    upper_exit_quantile: Decimal
    upper_quantile: Decimal

    def __post_init__(self) -> None:
        values = (
            self.lower_quantile,
            self.lower_exit_quantile,
            self.upper_exit_quantile,
            self.upper_quantile,
        )
        if any(not isinstance(value, Decimal) for value in values):
            raise TypeError("quantiles must be Decimal values")
        if not 0 <= self.lower_quantile < self.lower_exit_quantile < self.upper_exit_quantile < self.upper_quantile <= 1:
            raise ValueError("quantiles must satisfy 0 <= lower < lower_exit < upper_exit < upper <= 1")


def make_sensitivity_variants(
    config: DimensionConfig | None = None,
    *,
    delta: Decimal = Decimal("0.02"),
) -> tuple[SensitivityVariant, ...]:
    """Create a small symmetric neighborhood around the configured thresholds."""
    base = config or DimensionConfig()
    if not isinstance(delta, Decimal) or delta <= 0:
        raise ValueError("delta must be a positive Decimal")

    candidates = (
        ("baseline", 0, 0, 0, 0),
        ("lower_entry_minus", -1, 0, 0, 0),
        ("lower_exit_minus", 0, -1, 0, 0),
        ("upper_exit_plus", 0, 0, 1, 0),
        ("upper_entry_plus", 0, 0, 0, 1),
        ("wider_band", -1, -1, 1, 1),
        ("narrower_band", 1, 1, -1, -1),
    )
    variants: list[SensitivityVariant] = []
    for name, lower, lower_exit, upper_exit, upper in candidates:
        values = (
            base.lower_quantile + delta * lower,
            base.lower_exit_quantile + delta * lower_exit,
            base.upper_exit_quantile + delta * upper_exit,
            base.upper_quantile + delta * upper,
        )
        if 0 <= values[0] < values[1] < values[2] < values[3] <= 1:
            variants.append(SensitivityVariant(name, *values))
    return tuple(variants)


def apply_variant(base: DimensionConfig, variant: SensitivityVariant) -> DimensionConfig:
    """Return a dimension configuration with only quantiles changed."""
    return DimensionConfig(
        lower_quantile=variant.lower_quantile,
        lower_exit_quantile=variant.lower_exit_quantile,
        upper_exit_quantile=variant.upper_exit_quantile,
        upper_quantile=variant.upper_quantile,
        min_observations=base.min_observations,
        confirmation_bars=base.confirmation_bars,
    )


@dataclass(frozen=True)
class StateDurationSummary:
    median: Decimal | None
    upper_tail: Decimal | None
    count: int


@dataclass(frozen=True)
class SensitivitySummary:
    observations: int
    missing: int
    trend_frequencies: dict[str, Decimal]
    transition_frequency: Decimal
    rapid_flip_count: int
    duration: StateDurationSummary
    baseline_agreement: Decimal | None


def summarize_states(
    states: Sequence[MarketState | None],
    *,
    baseline: Sequence[MarketState | None] | None = None,
    rapid_flip_window: int = 1,
) -> SensitivitySummary:
    """Summarize classifier behavior without evaluating trading performance."""
    if rapid_flip_window <= 0:
        raise ValueError("rapid_flip_window must be positive")
    observed = [state for state in states if state is not None]
    missing = len(states) - len(observed)
    if not states:
        return SensitivitySummary(0, 0, {}, Decimal(0), 0, StateDurationSummary(None, None, 0), None)

    counts = Counter(state.trend.value for state in observed)
    frequencies = {
        trend.value: Decimal(counts.get(trend.value, 0)) / Decimal(len(observed))
        for trend in TrendState
    }
    transitions = sum(
        state.transition
        not in {
            Transition.PERSISTING_UP,
            Transition.PERSISTING_NEUTRAL,
            Transition.PERSISTING_DOWN,
        }
        for state in observed
    )
    transition_frequency = Decimal(transitions) / Decimal(len(observed))

    durations: list[int] = []
    current_trend: TrendState | None = None
    current_duration = 0
    for state in observed:
        if state.trend is current_trend:
            current_duration += 1
        else:
            if current_duration:
                durations.append(current_duration)
            current_trend = state.trend
            current_duration = 1
    if current_duration:
        durations.append(current_duration)

    sorted_durations = sorted(durations)
    tail = sorted_durations[max(0, int(len(sorted_durations) * 0.9) - 1):]
    duration_summary = StateDurationSummary(
        Decimal(str(median(sorted_durations))) if sorted_durations else None,
        Decimal(str(median(tail))) if tail else None,
        len(sorted_durations),
    )

    rapid_flips = 0
    previous_trend: TrendState | None = None
    since_change = rapid_flip_window
    for state in observed:
        if previous_trend is not None and state.trend is not previous_trend:
            if since_change <= rapid_flip_window:
                rapid_flips += 1
            since_change = 0
        since_change += 1
        previous_trend = state.trend

    agreement: Decimal | None = None
    if baseline is not None:
        if len(baseline) != len(states):
            raise ValueError("baseline and states must have equal lengths")
        comparable = 0
        matches = 0
        for left, right in zip(states, baseline):
            if left is None or right is None:
                continue
            comparable += 1
            if left.trend is right.trend:
                matches += 1
        if comparable:
            agreement = Decimal(matches) / Decimal(comparable)

    return SensitivitySummary(
        observations=len(observed),
        missing=missing,
        trend_frequencies=frequencies,
        transition_frequency=transition_frequency,
        rapid_flip_count=rapid_flips,
        duration=duration_summary,
        baseline_agreement=agreement,
    )
