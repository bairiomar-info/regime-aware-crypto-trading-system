from decimal import Decimal

import pytest

from trading_system.regime import (
    DimensionConfig,
    LevelState,
    MarketState,
    SensitivityVariant,
    StateDurationSummary,
    TrendState,
    Transition,
    apply_variant,
    make_sensitivity_variants,
    summarize_states,
)


def _state(trend: TrendState, transition: Transition, age: int = 1) -> MarketState:
    return MarketState(
        decision_time=None,
        trend=trend,
        volatility=LevelState.NORMAL,
        breadth=LevelState.NORMAL,
        dispersion=LevelState.NORMAL,
        correlation=LevelState.NORMAL,
        transition=transition,
        state_age=age,
        confidence=Decimal("1"),
    )


def test_variants_include_baseline_and_are_valid():
    variants = make_sensitivity_variants()
    assert variants[0].name == "baseline"
    assert len(variants) >= 5
    for variant in variants:
        assert 0 <= variant.lower_quantile < variant.lower_exit_quantile
        assert variant.lower_exit_quantile < variant.upper_exit_quantile < variant.upper_quantile <= 1


def test_variant_delta_must_be_positive():
    with pytest.raises(ValueError, match="delta must be positive"):
        make_sensitivity_variants(delta=Decimal("0"))


def test_variant_preserves_non_quantile_dimension_config():
    base = DimensionConfig(min_observations=17, confirmation_bars=4)
    variant = make_sensitivity_variants(base)[-1]
    result = apply_variant(base, variant)
    assert result.min_observations == 17
    assert result.confirmation_bars == 4
    assert result.lower_quantile == variant.lower_quantile


def test_sensitivity_variant_rejects_invalid_ordering():
    with pytest.raises(ValueError, match="quantiles must satisfy"):
        SensitivityVariant(
            "bad",
            Decimal("0.40"),
            Decimal("0.30"),
            Decimal("0.60"),
            Decimal("0.70"),
        )


def test_summary_counts_states_transitions_and_missing_values():
    states = [
        _state(TrendState.UP, Transition.PERSISTING_UP),
        _state(TrendState.UP, Transition.PERSISTING_UP),
        None,
        _state(TrendState.DOWN, Transition.UP_TO_DOWN),
    ]
    summary = summarize_states(states)
    assert summary.observations == 3
    assert summary.missing == 1
    assert summary.trend_frequencies["UP"] == Decimal(2) / Decimal(3)
    assert summary.trend_frequencies["DOWN"] == Decimal(1) / Decimal(3)
    assert summary.transition_frequency == Decimal(1) / Decimal(3)
    assert summary.duration == StateDurationSummary(Decimal("2"), Decimal("2"), 2)


def test_summary_measures_baseline_agreement_only_on_comparable_states():
    baseline = [
        _state(TrendState.UP, Transition.PERSISTING_UP),
        None,
        _state(TrendState.DOWN, Transition.PERSISTING_DOWN),
    ]
    candidate = [
        _state(TrendState.UP, Transition.PERSISTING_UP),
        _state(TrendState.DOWN, Transition.PERSISTING_DOWN),
        _state(TrendState.UP, Transition.DOWN_TO_UP),
    ]
    summary = summarize_states(candidate, baseline=baseline)
    assert summary.baseline_agreement == Decimal("0.5")


def test_summary_rejects_different_baseline_lengths():
    with pytest.raises(ValueError, match="equal lengths"):
        summarize_states([_state(TrendState.UP, Transition.PERSISTING_UP)], baseline=[])


def test_empty_summary_is_deterministic():
    assert summarize_states([]).trend_frequencies == {}
    assert summarize_states([]).duration.median is None
    assert summarize_states([]).baseline_agreement is None
