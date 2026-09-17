from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig
from trading_system.backtest.oos_experiments import run_oos_experiments
from trading_system.backtest.results import BacktestResult, EquityPoint
from trading_system.backtest.robustness import SensitivityCase


def _result(case: str, index: int) -> BacktestResult:
    if case == "baseline":
        total_return = Decimal("0.01") * Decimal(index + 1)
    else:
        total_return = (Decimal("0.02"), Decimal("-0.01"), Decimal("0.04"))[index]
    initial = Decimal("100")
    final = initial * (Decimal("1") + total_return)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return BacktestResult(
        initial_cash=initial,
        final_cash=final,
        final_quantity=Decimal("0"),
        final_equity=final,
        total_return=total_return,
        max_drawdown=Decimal("0.01"),
        equity_curve=(
            EquityPoint(start, initial),
            EquityPoint(start + timedelta(hours=1), final),
        ),
    )


def test_multiple_cases_and_windows_are_aggregated() -> None:
    cases = (
        SensitivityCase("baseline", BacktestConfig(initial_cash=Decimal("100"))),
        SensitivityCase("variant", BacktestConfig(initial_cash=Decimal("100"))),
    )

    def runner(case: SensitivityCase, index: int) -> BacktestResult:
        return _result(case.name, index)

    output = run_oos_experiments(cases, runner, 3)
    assert len(output) == 2
    assert [item.case_name for item in output] == ["baseline", "variant"]
    assert [len(item.windows) for item in output] == [3, 3]
    assert output[1].windows[1].total_return == Decimal("-0.01")


def test_empty_cases_are_rejected() -> None:
    with pytest.raises(ValueError, match="cases must not be empty"):
        run_oos_experiments((), lambda case, index: _result("baseline", index), 1)


def test_non_positive_window_count_is_rejected() -> None:
    with pytest.raises(ValueError, match="window_count must be positive"):
        run_oos_experiments(
            (SensitivityCase("baseline", BacktestConfig(initial_cash=Decimal("100"))),),
            lambda case, index: _result("baseline", index),
            0,
        )
