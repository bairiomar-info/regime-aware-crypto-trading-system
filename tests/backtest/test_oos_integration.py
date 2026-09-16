from decimal import Decimal

from trading_system.backtest.oos_experiments import run_oos_experiments
from trading_system.backtest.results import BacktestResult
from trading_system.backtest.robustness import SensitivityCase
from trading_system.backtest.engine import BacktestConfig


def _result(index: int) -> BacktestResult:
    return BacktestResult(
        total_return=Decimal("0.01") * (index + 1),
        max_drawdown=Decimal("0.02"),
        trades=(),
        equity_curve=(),
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
