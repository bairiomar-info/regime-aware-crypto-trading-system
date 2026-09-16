from datetime import datetime, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def test_long_execution_applies_fee_and_slippage() -> None:
    decision = datetime(2026, 9, 16, tzinfo=timezone.utc)
    execution = MarketBar(
        timestamp=datetime(2026, 9, 16, 1, tzinfo=timezone.utc),
        open=Decimal("100"),
        close=Decimal("100"),
    )
    signal = StrategySignal(
        decision_time=decision,
        direction=SignalDirection.LONG,
        target_weight=Decimal("1"),
    )
    state = execute_signal(
        BacktestState(cash=Decimal("1000"), quantity=Decimal("0")),
        signal,
        execution,
        BacktestConfig(
            initial_cash=Decimal("1000"),
            fee_rate=Decimal("0.01"),
            slippage_rate=Decimal("0.01"),
        ),
    )

    assert state.quantity == Decimal("9.803921568627450980392156863")
    assert state.cash == Decimal("0")
