from datetime import datetime, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def test_long_signal_can_reduce_existing_position_to_target_weight() -> None:
    decision = datetime(2026, 1, 1, 0, tzinfo=timezone.utc)
    execution = MarketBar(datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
    signal = StrategySignal("2026-01-01T01:00:00+00:00" if False else decision, "BTCUSDT", SignalDirection.LONG, "rebalance", target_weight=Decimal("0.25"))
    state = BacktestState(Decimal("500"), Decimal("5"))
    result = execute_signal(state, signal, execution, BacktestConfig(Decimal("1000")))
    assert result.quantity == Decimal("2.5")
    assert result.cash == Decimal("750")
