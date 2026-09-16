from decimal import Decimal

import pytest

from trading_system.regime.thresholds import (
    classify_three_level,
    classify_three_level_hysteresis,
    classify_trend,
    classify_trend_hysteresis,
    empirical_quantile,
)


def test_empirical_quantile_is_deterministic() -> None:
    assert empirical_quantile(["1", "2", "3", "4"], "0.5") == Decimal("2.5")


def test_empirical_quantile_empty_returns_none() -> None:
    assert empirical_quantile([], "0.5") is None


def test_empirical_quantile_rejects_invalid_quantile() -> None:
    with pytest.raises(ValueError):
        empirical_quantile(["1", "2"], "1.1")


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_empirical_quantile_rejects_non_finite_values(value: str) -> None:
    with pytest.raises(ValueError, match="finite"):
        empirical_quantile(["1", value, "2"], "0.5")


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_classifiers_reject_non_finite_values(value: str) -> None:
    with pytest.raises(ValueError, match="finite"):
        classify_three_level(value, low_entry="1", high_entry="3")
    with pytest.raises(ValueError, match="finite"):
        classify_trend(value, down_entry="-1", up_entry="1")


def test_three_level_hysteresis_holds_low_until_exit() -> None:
    kwargs = dict(low_entry="2", low_exit="2.5", high_exit="7.5", high_entry="8")
    assert classify_three_level_hysteresis("2.4", accepted_state="LOW", **kwargs) == "LOW"
    assert classify_three_level_hysteresis("2.5", accepted_state="LOW", **kwargs) == "NORMAL"


def test_trend_hysteresis_holds_up_until_exit() -> None:
    kwargs = dict(down_entry="-2", down_exit="-1.5", up_exit="1.5", up_entry="2")
    assert classify_trend_hysteresis("1.6", accepted_state="UP", **kwargs) == "UP"
    assert classify_trend_hysteresis("1.5", accepted_state="UP", **kwargs) == "NORMAL"


def test_boundary_order_is_required() -> None:
    with pytest.raises(ValueError):
        classify_three_level_hysteresis(
            "5",
            accepted_state=None,
            low_entry="2",
            low_exit="1",
            high_exit="7",
            high_entry="8",
        )
    with pytest.raises(ValueError):
        classify_trend_hysteresis(
            "0",
            accepted_state=None,
            down_entry="-2",
            down_exit="-1",
            up_exit="2",
            up_entry="1",
        )
