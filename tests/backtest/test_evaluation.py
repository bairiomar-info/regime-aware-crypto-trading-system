from decimal import Decimal

import pytest

from trading_system.backtest.evaluation import OOSWindowResult, summarize_oos


def test_summarize_oos_compounds_window_returns() -> None:
    summary = summarize_oos((
        OOSWindowResult(0, Decimal("0.10"), Decimal("0.05")),
        OOSWindowResult(1, Decimal("-0.05"), Decimal("0.08")),
    ))
    assert summary.compounded_return == Decimal("0.045")
    assert summary.worst_drawdown == Decimal("0.08")


def test_summarize_oos_rejects_duplicate_window_index() -> None:
    with pytest.raises(ValueError):
        summarize_oos((OOSWindowResult(0, Decimal("0"), Decimal("0")), OOSWindowResult(0, Decimal("0"), Decimal("0"))))
