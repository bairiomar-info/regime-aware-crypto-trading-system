from datetime import datetime, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def test_long_execution_applies_fee_and_slippage() -> None:
    decision = datetime(2026, 9, 16, tzinfo=timezone.utc)
    execution = MarketBar(datetime(2026, 9, 16, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
    signal = StrategySignal(decision_time=decision, symbol="BTCUSDT", direction=SignalDirection.LONG, reason="cost test", target_weight=Decimal("1"))
    state = execute_signal(
        BacktestState(Decimal("1000"), Decimal("0")), signal, execution,
        BacktestConfig(Decimal("1000"), fee_rate=Decimal("0.01"), slippage_rate=Decimal("0.01")),
    )
    expected_price = Decimal("101")
    expected_quantity = Decimal("1000") / (expected_price * Decimal("1.01"))
    assert state.quantity == expected_quantity
    assert state.cash >= 0
