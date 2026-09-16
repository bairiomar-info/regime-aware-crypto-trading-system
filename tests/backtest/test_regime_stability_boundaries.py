from decimal import Decimal

import pytest

from trading_system.backtest.evaluation import OOSWindowResult
from trading_system.backtest.regime_stability import analyze_by_regime


def _window(index: int, value: str, drawdown: str = "0.02") -> OOSWindowResult:
    return OOSWindowResult(index, Decimal(value), Decimal(drawdown))


def test_regime_analysis_groups_and_sorts_regimes_deterministically() -> None:
    results = analyze_by_regime(
        (
            ("bull", _window(0, "0.10")),
            ("bear", _window(1, "-0.02", "0.08")),
            ("bull", _window(2, "0.04")),
        )
    )
    assert [item.regime for item in results] == ["bear", "bull"]
    assert results[0].window_count == 1
    assert results[0].positive_window_fraction == Decimal("0")
    assert results[0].worst_return == Decimal("-0.02")
    assert results[1].window_count == 2
    assert results[1].positive_window_fraction == Decimal("1")
    assert results[1].mean_return == Decimal("0.07")


def test_empty_regime_label_is_rejected() -> None:
    with pytest.raises(ValueError, match="regime must not be empty"):
        analyze_by_regime((("", _window(0, "0.01")),))


def test_empty_windows_are_rejected() -> None:
    with pytest.raises(ValueError, match="windows must not be empty"):
        analyze_by_regime(())


def test_regime_drawdown_uses_worst_window_drawdown() -> None:
    results = analyze_by_regime(
        (
            ("bear", _window(0, "0.01", "0.03")),
            ("bear", _window(1, "0.02", "0.11")),
        )
    )
    assert results[0].worst_drawdown == Decimal("0.11")
