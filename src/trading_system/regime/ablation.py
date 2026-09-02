"""Descriptive ablation contracts for the V1 regime dimensions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping, Sequence

from .models import LevelState, TrendState


class AblationVariant(str, Enum):
    TREND_ONLY = "trend_only"
    TREND_VOLATILITY = "trend_volatility"
    TREND_BREADTH = "trend_breadth"
    TREND_DISPERSION = "trend_dispersion"
    TREND_CORRELATION = "trend_correlation"
    ALL_FIVE = "all_five"


@dataclass(frozen=True)
class AblationSpec:
    name: AblationVariant
    dimensions: tuple[str, ...]


_PRE_REGISTERED = (
    AblationSpec(AblationVariant.TREND_ONLY, ("trend",)),
    AblationSpec(AblationVariant.TREND_VOLATILITY, ("trend", "volatility")),
    AblationSpec(AblationVariant.TREND_BREADTH, ("trend", "breadth")),
    AblationSpec(AblationVariant.TREND_DISPERSION, ("trend", "dispersion")),
    AblationSpec(AblationVariant.TREND_CORRELATION, ("trend", "correlation")),
    AblationSpec(
        AblationVariant.ALL_FIVE,
        ("trend", "volatility", "breadth", "dispersion", "correlation"),
    ),
)


def pre_registered_ablation_specs() -> tuple[AblationSpec, ...]:
    """Return the fixed V1 ablation set in deterministic order."""
    return _PRE_REGISTERED


def state_signature(
    states: Mapping[str, str | TrendState | LevelState | None],
    spec: AblationSpec,
) -> tuple[tuple[str, str | None], ...]:
    """Return a deterministic signature containing only enabled dimensions."""
    return tuple(
        (
            dimension,
            None
            if states.get(dimension) is None
            else str(
                states[dimension].value
                if isinstance(states[dimension], Enum)
                else states[dimension]
            ),
        )
        for dimension in spec.dimensions
    )


@dataclass(frozen=True)
class AblationComparison:
    observations: int
    comparable: int
    agreements: int
    agreement_ratio: Decimal | None


def compare_shared_dimensions(
    candidate: Sequence[Mapping[str, str | TrendState | LevelState | None]],
    baseline: Sequence[Mapping[str, str | TrendState | LevelState | None]],
    spec: AblationSpec,
) -> AblationComparison:
    """Compare only dimensions explicitly present in an ablation spec."""
    if len(candidate) != len(baseline):
        raise ValueError("candidate and baseline must have equal lengths")
    observations = len(candidate)
    comparable = 0
    agreements = 0
    for left, right in zip(candidate, baseline):
        left_sig = state_signature(left, spec)
        right_sig = state_signature(right, spec)
        if any(value is None for _, value in left_sig + right_sig):
            continue
        comparable += 1
        if left_sig == right_sig:
            agreements += 1
    ratio = Decimal(agreements) / Decimal(comparable) if comparable else None
    return AblationComparison(observations, comparable, agreements, ratio)
