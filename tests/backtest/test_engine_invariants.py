from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def make_signal(timestamp: datetime, target_weight: str = "1") -> StrategySignal:
    return StrategySignal(
        decision_time=timestamp,
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        reason="test",
        target_weight=Decimal(target_weight),
    )


def test_buy_never_creates_negative_cash() -> None:
    decision = datetime(2026, 1, 1, 0, tzinfo=timezone.utc)
    bar = MarketBar(datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
    result = execute_signal(
        BacktestState(Decimal("10"), Decimal("0")),
        make_signal(decision),
        bar,
        BacktestConfig(Decimal("10"), Decimal("0.01")),
    )
    assert result.cash >= 0
    assert result.quantity >= 0


def test_execution_must_be_after_decision() -> None:
    timestamp = datetime(2026, 1, 1, 1, tzinfo=timezone.utc)
    bar = MarketBar(timestamp, Decimal("100"), Decimal("100"))
    with pytest.raises(ValueError, match="strictly after"):
        execute_signal(
            BacktestState(Decimal("100"), Decimal("0")),
            make_signal(timestamp),
            bar,
            BacktestConfig(Decimal("100")),
        )


def test_target_weight_one_with_existing_position_never_exceeds_equity() -> None:
    decision = datetime(2026, 1, 1, 0, tzinfo=timezone.utc)
    bar = MarketBar(datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
    state = BacktestState(Decimal("500"), Decimal("5"))
    result = execute_signal(
        state,
        make_signal(decision),
        bar,
        BacktestConfig(Decimal("1000"), fee_rate=Decimal("0.01"), slippage_rate=Decimal("0.01")),
    )
    marked_equity = result.cash + result.quantity * bar.close
    assert result.cash >= 0
    assert result.quantity >= 0
    assert marked_equity <= Decimal("1000")


def test_zero_fee_zero_slippage_full_rebalance_is_conservative() -> None:
    decision = datetime(2026, 1, 1, 0, tzinfo=timezone.utc)
    bar = MarketBar(datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
    result = execute_signal(
        BacktestState(Decimal("500"), Decimal("5")),
        make_signal(decision, "0.5"),
        bar,
        BacktestConfig(Decimal("1000")),
    )
    assert result.cash == Decimal("500")
    assert result.quantity == Decimal("5")
