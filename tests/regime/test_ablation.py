from decimal import Decimal

import pytest

from trading_system.regime import (
    AblationVariant,
    LevelState,
    TrendState,
    compare_shared_dimensions,
    pre_registered_ablation_specs,
    state_signature,
)


def test_pre_registered_ablation_set_is_fixed_and_ordered():
    specs = pre_registered_ablation_specs()
    assert [spec.name for spec in specs] == [
        AblationVariant.TREND_ONLY,
        AblationVariant.TREND_VOLATILITY,
        AblationVariant.TREND_BREADTH,
        AblationVariant.TREND_DISPERSION,
        AblationVariant.TREND_CORRELATION,
        AblationVariant.ALL_FIVE,
    ]
    assert specs[0].dimensions == ("trend",)
    assert specs[-1].dimensions == (
        "trend",
        "volatility",
        "breadth",
        "dispersion",
        "correlation",
    )


def test_state_signature_is_deterministic_and_uses_only_enabled_dimensions():
    spec = pre_registered_ablation_specs()[1]
    states = {
        "trend": TrendState.UP,
        "volatility": LevelState.HIGH,
        "breadth": LevelState.LOW,
        "dispersion": LevelState.NORMAL,
        "correlation": LevelState.HIGH,
    }
    assert state_signature(states, spec) == (
        ("trend", "UP"),
        ("volatility", "HIGH"),
    )


def test_state_signature_preserves_missingness():
    spec = pre_registered_ablation_specs()[2]
    states = {"trend": TrendState.UP, "breadth": None}
    assert state_signature(states, spec) == (("trend", "UP"), ("breadth", None))


def test_compare_shared_dimensions_ignores_unshared_dimensions():
    spec = pre_registered_ablation_specs()[0]
    baseline = [
        {"trend": TrendState.UP, "volatility": LevelState.NORMAL},
        {"trend": TrendState.DOWN, "volatility": LevelState.HIGH},
    ]
    candidate = [
        {"trend": TrendState.UP, "volatility": LevelState.LOW},
        {"trend": TrendState.DOWN, "volatility": LevelState.NORMAL},
    ]
    result = compare_shared_dimensions(candidate, baseline, spec)
    assert result.observations == 2
    assert result.comparable == 2
    assert result.agreements == 2
    assert result.agreement_ratio == Decimal("1")


def test_compare_shared_dimensions_counts_only_complete_comparisons():
    spec = pre_registered_ablation_specs()[1]
    baseline = [
        {"trend": TrendState.UP, "volatility": LevelState.NORMAL},
        {"trend": TrendState.DOWN, "volatility": None},
        {"trend": TrendState.UP, "volatility": LevelState.HIGH},
    ]
    candidate = [
        {"trend": TrendState.UP, "volatility": LevelState.HIGH},
        {"trend": TrendState.DOWN, "volatility": LevelState.HIGH},
        {"trend": TrendState.DOWN, "volatility": LevelState.HIGH},
    ]
    result = compare_shared_dimensions(candidate, baseline, spec)
    assert result.observations == 3
    assert result.comparable == 2
    assert result.agreements == 1
    assert result.agreement_ratio == Decimal("0.5")


def test_compare_shared_dimensions_reports_no_comparable_observations():
    spec = pre_registered_ablation_specs()[1]
    baseline = [{"trend": TrendState.UP, "volatility": None}]
    candidate = [{"trend": TrendState.UP, "volatility": None}]
    result = compare_shared_dimensions(candidate, baseline, spec)
    assert result.comparable == 0
    assert result.agreement_ratio is None


def test_compare_shared_dimensions_requires_equal_lengths():
    spec = pre_registered_ablation_specs()[0]
    with pytest.raises(ValueError, match="equal lengths"):
        compare_shared_dimensions([{"trend": TrendState.UP}], [], spec)
