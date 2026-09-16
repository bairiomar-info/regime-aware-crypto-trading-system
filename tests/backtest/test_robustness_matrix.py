from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.parameter_sensitivity import MomentumParameterCase
from trading_system.backtest.results import BacktestResult, EquityPoint
from trading_system.backtest.robustness_matrix import run_momentum_cost_matrix
from trading_system.strategies.momentum import TimeSeriesMomentumConfig


def test_matrix_executes_every_parameter_cost_combination() -> None:
    bar = MarketBar.__new__(MarketBar)
    bars = (bar,)
    parameters = (
        MomentumParameterCase("p1", TimeSeriesMomentumConfig(5, Decimal("0.5"), Decimal("0"))),
        MomentumParameterCase("p2", TimeSeriesMomentumConfig(10, Decimal("0.5"), Decimal("0"))),
    )
    costs = (("base", BacktestConfig(initial_cash=Decimal("100"))), ("stress", BacktestConfig(initial_cash=Decimal("100"), fee_rate=Decimal("0.01"))))
    result = BacktestResult(Decimal("100"), Decimal("100"), Decimal("0"), Decimal("100"), Decimal("0"), Decimal("0"), (EquityPoint.__new__(EquityPoint),))
    matrix = run_momentum_cost_matrix(bars, parameters, costs, lambda *_: result)
    assert len(matrix.cases) == 4
    assert matrix.cases[0].name == "p1|base"
    assert matrix.cases[-1].name == "p2|stress"
    assert matrix.summary.case_count == 4
