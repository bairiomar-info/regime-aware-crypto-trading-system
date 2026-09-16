from decimal import Decimal

from trading_system.backtest.evaluation import OOSWindowResult
from trading_system.backtest.regime_stability import analyze_by_regime


def test_analyze_by_regime_groups_and_sorts_regimes() -> None:
    rows = (
        ("high_vol", OOSWindowResult(1, Decimal("-0.02"), Decimal("0.20"))),
        ("trend", OOSWindowResult(0, Decimal("0.10"), Decimal("0.05"))),
        ("trend", OOSWindowResult(2, Decimal("0.04"), Decimal("0.10"))),
    )
    result = analyze_by_regime(rows)
    assert [item.regime for item in result] == ["high_vol", "trend"]
    assert result[1].window_count == 2
    assert result[1].positive_window_fraction == Decimal("1")
    assert result[1].mean_return == Decimal("0.07")


def test_analyze_by_regime_rejects_empty_label() -> None:
    try:
        analyze_by_regime((("", OOSWindowResult(0, Decimal("0"), Decimal("0"))),))
    except ValueError as exc:
        assert str(exc) == "regime must not be empty"
    else:
        raise AssertionError("expected ValueError")
