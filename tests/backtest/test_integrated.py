from datetime import datetime, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.integrated import IntegratedBacktestInput, run_strategy_backtest
from trading_system.strategies.momentum import TimeSeriesMomentum, TimeSeriesMomentumConfig
from trading_system.strategies.models import StrategyContext


def test_integrated_strategy_backtest_respects_next_bar_execution() -> None:
    bars = tuple(
        MarketBar(datetime(2026, 1, 1, h, tzinfo=timezone.utc), Decimal(str(p)), Decimal(str(p)))
        for h, p in ((0, 100), (1, 110), (2, 120))
    )
    contexts = (
        StrategyContext(
            decision_time=bars[1].timestamp,
            symbol="BTCUSDT",
            price_history=((bars[0].timestamp, Decimal("100")), (bars[1].timestamp, Decimal("110"))),
        ),
    )
    strategy = TimeSeriesMomentum(TimeSeriesMomentumConfig(lookback=1, target_weight=Decimal("1")))
    result = run_strategy_backtest(strategy, IntegratedBacktestInput(bars, contexts), BacktestConfig(Decimal("1000")))
    # Signal is evaluated at t=1 and therefore can only execute at t=2.
    assert result.equity_curve[1].equity == Decimal("1000")
    assert result.final_equity == Decimal("1000")
