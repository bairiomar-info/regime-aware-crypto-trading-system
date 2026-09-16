from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def make_signal(timestamp: datetime) -> StrategySignal:
    return StrategySignal(decision_time=timestamp, symbol="BTCUSDT", direction=SignalDirection.LONG, reason="test", target_weight=Decimal("1"))


def test_buy_never_creates_negative_cash() -> None:
    decision = datetime(2026, 1, 1, 0, tzinfo=timezone.utc)
    bar = MarketBar(datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
    result = execute_signal(BacktestState(Decimal("10"), Decimal("0")), make_signal(decision), bar, BacktestConfig(Decimal("10"), Decimal("0.01")))
    assert result.cash >= 0


def test_execution_must_be_after_decision() -> None:
    timestamp = datetime(2026, 1, 1, 1, tzinfo=timezone.utc)
    bar = MarketBar(timestamp, Decimal("100"), Decimal("100"))
    with pytest.raises(ValueError, match="strictly after"):
        execute_signal(BacktestState(Decimal("100"), Decimal("0")), make_signal(timestamp), bar, BacktestConfig(Decimal("100")))
