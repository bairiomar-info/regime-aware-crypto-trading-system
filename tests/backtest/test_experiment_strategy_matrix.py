from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.experiment import ExperimentCase, run_strategy_experiment_matrix
from trading_system.backtest.integrated import IntegratedBacktestInput
from trading_system.features.models import FeatureSnapshot
from trading_system.strategies.momentum import TimeSeriesMomentum, TimeSeriesMomentumConfig
from trading_system.strategies.models import StrategyContext


def _context(timestamp: datetime, history: tuple[tuple[datetime, Decimal], ...]) -> StrategyContext:
    return StrategyContext(
        decision_time=timestamp,
        symbol="BTCUSDT",
        features=FeatureSnapshot(
            decision_time=timestamp,
            trend_score=None,
            realized_volatility=None,
            breadth=None,
            cross_sectional_dispersion=None,
            average_pairwise_correlation=None,
            asset_count=1,
        ),
        price_history=history,
    )


def test_strategy_experiment_matrix_uses_canonical_backtest_path() -> None:
    bars = tuple(
        MarketBar(datetime(2026, 1, 1, h, tzinfo=timezone.utc), Decimal(str(price)), Decimal(str(price)))
        for h, price in ((0, 100), (1, 110), (2, 120))
    )
    contexts = (_context(bars[1].timestamp, ((bars[0].timestamp, Decimal("100")), (bars[1].timestamp, Decimal("110")))),)
    case = ExperimentCase(
        "momentum",
        BacktestConfig(Decimal("1000")),
        TimeSeriesMomentumConfig(lookback=1, target_weight=Decimal("1")),
    )

    results = run_strategy_experiment_matrix(
        bars,
        contexts,
        (case,),
        lambda config: TimeSeriesMomentum(config),
    )

    assert results[0].name == "momentum"
    assert results[0].total_return == Decimal("0")
    assert results[0].max_drawdown == Decimal("0")


def test_strategy_experiment_matrix_rejects_empty_inputs() -> None:
    bars = (MarketBar(datetime(2026, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100")),)
    context = _context(bars[0].timestamp, ((bars[0].timestamp, Decimal("100")),))

    with pytest.raises(ValueError, match="cases must not be empty"):
        run_strategy_experiment_matrix(bars, (context,), (), lambda config: TimeSeriesMomentum(config))

    with pytest.raises(ValueError, match="contexts must not be empty"):
        run_strategy_experiment_matrix(bars, (), (ExperimentCase("x", BacktestConfig(Decimal("1000"))),), lambda config: TimeSeriesMomentum(config))

    with pytest.raises(ValueError, match="bars must not be empty"):
        run_strategy_experiment_matrix((), (context,), (ExperimentCase("x", BacktestConfig(Decimal("1000"))),), lambda config: TimeSeriesMomentum(config))
