"""Causal V1 multidimensional regime classifier."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from types import MappingProxyType

from .hysteresis import HysteresisConfig, update_hysteresis
from .models import LevelState, MarketState, TrendState
from .state import evidence_confidence, transition_for
from .thresholds import (
    classify_three_level_hysteresis,
    classify_trend_hysteresis,
    empirical_quantile,
)


class Dimension(str, Enum):
    TREND = "trend"
    VOLATILITY = "volatility"
    BREADTH = "breadth"
    DISPERSION = "dispersion"
    CORRELATION = "correlation"


@dataclass(frozen=True)
class DimensionConfig:
    lower_quantile: Decimal = Decimal("0.33")
    lower_exit_quantile: Decimal = Decimal("0.40")
    upper_exit_quantile: Decimal = Decimal("0.60")
    upper_quantile: Decimal = Decimal("0.67")
    min_observations: int = 30
    confirmation_bars: int = 2

    def __post_init__(self) -> None:
        if not (
            Decimal("0") <= self.lower_quantile < self.lower_exit_quantile
            < self.upper_exit_quantile < self.upper_quantile <= Decimal("1")
        ):
            raise ValueError(
                "quantiles must satisfy 0 <= lower < lower_exit < upper_exit < upper <= 1"
            )
        if self.min_observations <= 0:
            raise ValueError("min_observations must be positive")
        if self.confirmation_bars <= 0:
            raise ValueError("confirmation_bars must be positive")


@dataclass(frozen=True)
class RegimeClassifierConfig:
    trend: DimensionConfig = field(default_factory=DimensionConfig)
    volatility: DimensionConfig = field(default_factory=DimensionConfig)
    breadth: DimensionConfig = field(default_factory=DimensionConfig)
    dispersion: DimensionConfig = field(default_factory=DimensionConfig)
    correlation: DimensionConfig = field(default_factory=DimensionConfig)

    def for_dimension(self, dimension: Dimension) -> DimensionConfig:
        return getattr(self, dimension.value)


@dataclass(frozen=True)
class DimensionTracker:
    state: str | None = None
    candidate_state: str | None = None
    confirmation_count: int = 0
    state_age: int = 0


@dataclass(frozen=True)
class RegimeClassifierState:
    dimensions: Mapping[str, DimensionTracker] = field(default_factory=dict)
    previous_trend: TrendState | None = None
    state_age: int = 0
    last_decision_time: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimensions", MappingProxyType(dict(self.dimensions)))
        if self.state_age < 0:
            raise ValueError("state_age must be non-negative")
        if self.last_decision_time is not None:
            _validate_utc(self.last_decision_time)


@dataclass(frozen=True)
class DimensionClassification:
    dimension: Dimension
    state: str | None
    sufficient_history: bool
    reference_count: int


@dataclass(frozen=True)
class RegimeClassificationResult:
    market_state: MarketState | None
    classifier_state: RegimeClassifierState
    dimensions: tuple[DimensionClassification, ...]


def classify_market_state(
    decision_time: datetime,
    current: Mapping[str, Decimal | str | None],
    history: Mapping[str, Sequence[Decimal | str]],
    *,
    previous: RegimeClassifierState | None = None,
    config: RegimeClassifierConfig | None = None,
    evidence: Sequence[bool | None] | None = None,
) -> RegimeClassificationResult:
    """Classify one point-in-time observation using only supplied past data."""
    _validate_utc(decision_time)
    cfg = config or RegimeClassifierConfig()
    old = previous or RegimeClassifierState()
    if old.last_decision_time is not None and decision_time <= old.last_decision_time:
        raise ValueError("decision_time must be strictly after previous last_decision_time")

    results: list[DimensionClassification] = []
    trackers: dict[str, DimensionTracker] = dict(old.dimensions)

    for dimension in Dimension:
        values = history.get(dimension.value, ())
        current_value = current.get(dimension.value)
        dim_cfg = cfg.for_dimension(dimension)
        reference_count = len(values)
        prior = old.dimensions.get(dimension.value, DimensionTracker())
        if current_value is None or reference_count < dim_cfg.min_observations:
            results.append(DimensionClassification(dimension, None, False, reference_count))
            continue

        lower = empirical_quantile(values, dim_cfg.lower_quantile)
        lower_exit = empirical_quantile(values, dim_cfg.lower_exit_quantile)
        upper_exit = empirical_quantile(values, dim_cfg.upper_exit_quantile)
        upper = empirical_quantile(values, dim_cfg.upper_quantile)
        if any(value is None for value in (lower, lower_exit, upper_exit, upper)):
            results.append(DimensionClassification(dimension, None, False, reference_count))
            continue
        assert lower is not None and lower_exit is not None and upper_exit is not None and upper is not None

        if dimension is Dimension.TREND:
            candidate = classify_trend_hysteresis(
                current_value,
                accepted_state=prior.state,
                down_entry=lower,
                down_exit=lower_exit,
                up_exit=upper_exit,
                up_entry=upper,
            )
        else:
            candidate = classify_three_level_hysteresis(
                current_value,
                accepted_state=prior.state,
                low_entry=lower,
                low_exit=lower_exit,
                high_exit=upper_exit,
                high_entry=upper,
            )
        if candidate is None:
            results.append(DimensionClassification(dimension, None, False, reference_count))
            continue

        stabilized = update_hysteresis(
            prior.state,
            candidate,
            confirmation_count=prior.confirmation_count,
            state_age=prior.state_age,
            config=HysteresisConfig(dim_cfg.confirmation_bars),
        )
        trackers[dimension.value] = DimensionTracker(
            state=stabilized.state,
            candidate_state=stabilized.candidate_state,
            confirmation_count=stabilized.confirmation_count,
            state_age=stabilized.state_age,
        )
        results.append(DimensionClassification(dimension, stabilized.state, True, reference_count))

    new_state = RegimeClassifierState(
        dimensions=trackers,
        previous_trend=old.previous_trend,
        state_age=old.state_age,
        last_decision_time=decision_time,
    )
    complete = all(item.state is not None and item.sufficient_history for item in results)
    if not complete:
        return RegimeClassificationResult(None, new_state, tuple(results))

    trend_state = TrendState(trackers[Dimension.TREND.value].state)
    transition = transition_for(trend_state, old.previous_trend)
    new_age = 1 if old.previous_trend is None or trend_state is not old.previous_trend else old.state_age + 1
    new_state = RegimeClassifierState(
        dimensions=trackers,
        previous_trend=trend_state,
        state_age=new_age,
        last_decision_time=decision_time,
    )
    confidence = evidence_confidence(evidence or ())
    market_state = MarketState(
        decision_time=decision_time,
        trend=trend_state,
        volatility=LevelState(trackers[Dimension.VOLATILITY.value].state),
        breadth=LevelState(trackers[Dimension.BREADTH.value].state),
        dispersion=LevelState(trackers[Dimension.DISPERSION.value].state),
        correlation=LevelState(trackers[Dimension.CORRELATION.value].state),
        transition=transition,
        state_age=new_age,
        confidence=confidence,
    )
    return RegimeClassificationResult(market_state, new_state, tuple(results))


def _validate_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("decision_time must be timezone-aware UTC")
