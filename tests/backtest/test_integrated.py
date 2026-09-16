from datetime import datetime, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.integrated import IntegratedBacktestInput, run_strategy_backtest
from trading_system.strategies.momentum import MomentumConfig, MomentumStrategy
from trading_system.strategies.models import StrategyContext


def test_integrated_strategy_backtest_respects_next_bar_execution() -> None:
    bars = tuple(
        MarketBar(datetime(2026, 1, 1, h, tzinfo=timezone.utc), Decimal(str(p)), Decimal(str(p)))
        for h, p in ((0, 100), (1, 110), (2, 120))
    )
    contexts = (
        StrategyContext(
            decision_time=bars[0].timestamp,
            symbol="BTCUSDT",
            price_history=((bars[0].timestamp, Decimal("100")),),
        ),
    )
    strategy = MomentumStrategy(MomentumConfig(lookback=1, threshold=Decimal("0"), target_weight=Decimal("1")))
    result = run_strategy_backtest(strategy, IntegratedBacktestInput(bars, contexts), BacktestConfig(Decimal("1000")))
    assert result.final_equity == Decimal("1090") or result.final_equity == Decimal("1100")
