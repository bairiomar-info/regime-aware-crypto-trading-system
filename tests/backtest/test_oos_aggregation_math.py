from decimal import Decimal

import pytest

from trading_system.backtest.evaluation import OOSWindowResult, summarize_oos


def _window(index: int, total_return: str, drawdown: str) -> OOSWindowResult:
    return OOSWindowResult(index, Decimal(total_return), Decimal(drawdown))


def test_compounded_return_is_multiplicative() -> None:
    summary = summarize_oos((_window(0, "0.10", "0.02"), _window(1, "0.20", "0.05")))
    assert summary.compounded_return == Decimal("0.32")


def test_worst_drawdown_is_the_maximum_stored_drawdown() -> None:
    summary = summarize_oos((_window(0, "0.01", "0.02"), _window(1, "0.02", "0.07"), _window(2, "0.03", "0.04")))
    assert summary.worst_drawdown == Decimal("0.07")


def test_out_of_order_windows_are_rejected() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        summarize_oos((_window(1, "0.01", "0.01"), _window(0, "0.02", "0.02")))


def test_total_return_below_minus_one_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid OOS metrics"):
        _window(0, "-1.01", "0.01")


def test_negative_drawdown_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid OOS metrics"):
        _window(0, "0.01", "-0.01")
