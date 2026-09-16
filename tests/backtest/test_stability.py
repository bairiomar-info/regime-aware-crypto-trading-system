from decimal import Decimal

from trading_system.backtest.evaluation import OOSWindowResult
from trading_system.backtest.stability import analyze_oos_stability


def test_analyze_oos_stability() -> None:
    windows = (
        OOSWindowResult(0, Decimal("0.10"), Decimal("0.05")),
        OOSWindowResult(1, Decimal("-0.02"), Decimal("0.20")),
        OOSWindowResult(2, Decimal("0.04"), Decimal("0.10")),
        OOSWindowResult(3, Decimal("0.08"), Decimal("0.07")),
    )
    result = analyze_oos_stability(windows)
    assert result.window_count == 4
    assert result.positive_window_fraction == Decimal("0.75")
    assert result.worst_return == Decimal("-0.02")
    assert result.worst_drawdown == Decimal("0.20")


def test_analyze_oos_stability_rejects_empty() -> None:
    try:
        analyze_oos_stability(())
    except ValueError as exc:
        assert str(exc) == "windows must not be empty"
    else:
        raise AssertionError("expected ValueError")
