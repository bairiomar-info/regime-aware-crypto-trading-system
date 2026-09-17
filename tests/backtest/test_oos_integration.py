from datetime import datetime, timedelta, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig
from trading_system.backtest.oos_experiments import run_oos_experiments
from trading_system.backtest.results import BacktestResult, EquityPoint
from trading_system.backtest.robustness import SensitivityCase


def _result(index: int) -> BacktestResult:
    total_return = Decimal("0.01") * Decimal(index + 1)
    initial = Decimal("100")
    final = initial * (Decimal("1") + total_return)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return BacktestResult(
        initial_cash=initial,
        final_cash=final,
        final_quantity=Decimal("0"),
        final_equity=final,
        total_return=total_return,
        max_drawdown=Decimal("0.02"),
        equity_curve=(
            EquityPoint(start, initial),
            EquityPoint(start + timedelta(hours=1), final),
        ),
    )


def test_oos_experiment_runs_every_case_on_every_window() -> None:
    cases = (
        SensitivityCase("case-a", BacktestConfig(initial_cash=Decimal("100"))),
        SensitivityCase("case-b", BacktestConfig(initial_cash=Decimal("100"))),
    )
    calls: list[tuple[str, int]] = []

    def runner(case: SensitivityCase, index: int) -> BacktestResult:
        calls.append((case.name, index))
        return _result(index)

    results = run_oos_experiments(cases, runner, window_count=3)

    assert calls == [("case-a", 0), ("case-a", 1), ("case-a", 2), ("case-b", 0), ("case-b", 1), ("case-b", 2)]
    assert results[0].compounded_return == Decimal("0.061106")
    assert results[0].worst_drawdown == Decimal("0.02")
