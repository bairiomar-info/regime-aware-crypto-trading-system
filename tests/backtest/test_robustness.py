from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig
from trading_system.backtest.results import BacktestResult, EquityPoint
from trading_system.backtest.robustness import make_cost_sensitivity_cases, summarize_sensitivity


def result(return_value: str) -> BacktestResult:
    return BacktestResult(
        initial_cash=Decimal("100"), final_cash=Decimal("110"), final_quantity=Decimal("0"), final_equity=Decimal("110"),
        total_return=Decimal(return_value), max_drawdown=Decimal("0.1"),
        equity_curve=(
            EquityPoint(datetime(2026, 1, 1, tzinfo=timezone.utc), Decimal("100")),
            EquityPoint(datetime(2026, 1, 2, tzinfo=timezone.utc), Decimal("110")),
        ),
    )


def test_cost_cases_are_deterministic_cartesian_product() -> None:
    cases = make_cost_sensitivity_cases(initial_cash=Decimal("1000"), fee_rates=(Decimal("0"), Decimal("0.001")), slippage_rates=(Decimal("0"), Decimal("0.002")))
    assert len(cases) == 4
    assert cases[0].config == BacktestConfig(initial_cash=Decimal("1000"))
    assert cases[-1].config.slippage_rate == Decimal("0.002")


def test_cost_cases_reject_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        make_cost_sensitivity_cases(initial_cash=Decimal("0"), fee_rates=(Decimal("0"),), slippage_rates=(Decimal("0"),))
    with pytest.raises(ValueError):
        make_cost_sensitivity_cases(initial_cash=Decimal("100"), fee_rates=(), slippage_rates=(Decimal("0"),))
    with pytest.raises(ValueError):
        make_cost_sensitivity_cases(initial_cash=Decimal("100"), fee_rates=(Decimal("1"),), slippage_rates=(Decimal("0"),))


def test_sensitivity_preserves_case_order() -> None:
    cases = make_cost_sensitivity_cases(initial_cash=Decimal("1000"), fee_rates=(Decimal("0"), Decimal("0.001")), slippage_rates=(Decimal("0"),))
    values = iter((result("0.1"), result("0.08")))
    def get_next_value(_):
        try:
            return next(values)
        except StopIteration:
            return None
    summary = summarize_sensitivity(cases, get_next_value)
    assert [item.name for item in summary] == [case.name for case in cases]
    assert summary[1].total_return == Decimal("0.08")


def test_sensitivity_rejects_empty_cases() -> None:
    with pytest.raises(ValueError):
        summarize_sensitivity((), lambda _: result("0"))
