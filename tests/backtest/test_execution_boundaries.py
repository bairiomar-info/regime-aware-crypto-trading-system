from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def _bar(hour: int, open_price: str = "100", close: str = "100") -> MarketBar:
    return MarketBar(datetime(2026, 9, 16, hour, tzinfo=timezone.utc), Decimal(open_price), Decimal(close))


def _signal(direction: SignalDirection, weight: str | None = "1") -> StrategySignal:
    return StrategySignal(
        decision_time=datetime(2026, 9, 16, tzinfo=timezone.utc),
        symbol="BTCUSDT", direction=direction, reason="test",
        target_weight=Decimal(weight) if weight is not None else None,
    )


def test_no_trade_preserves_state() -> None:
    state = BacktestState(Decimal("1000"), Decimal("2"))
    assert execute_signal(state, _signal(SignalDirection.NO_TRADE, None), _bar(1), BacktestConfig(Decimal("1000"))) == state


def test_long_uses_execution_bar_open() -> None:
    result = execute_signal(BacktestState(Decimal("1000"), Decimal("0")), _signal(SignalDirection.LONG), _bar(1, "125", "200"), BacktestConfig(Decimal("1000")))
    assert result.quantity == Decimal("8")
    assert result.cash == Decimal("0")


def test_long_target_weight_is_respected() -> None:
    result = execute_signal(BacktestState(Decimal("500"), Decimal("5")), _signal(SignalDirection.LONG, "0.5"), _bar(1), BacktestConfig(Decimal("1000")))
    assert result.quantity == Decimal("5")
    assert result.cash == Decimal("500")


def test_slippage_increases_long_entry_price() -> None:
    result = execute_signal(BacktestState(Decimal("1000"), Decimal("0")), _signal(SignalDirection.LONG), _bar(1), BacktestConfig(Decimal("1000"), slippage_rate=Decimal("0.10")))
    assert result.quantity == Decimal("1000") / Decimal("110")


def test_fee_reduces_long_quantity() -> None:
    result = execute_signal(BacktestState(Decimal("1000"), Decimal("0")), _signal(SignalDirection.LONG), _bar(1), BacktestConfig(Decimal("1000"), fee_rate=Decimal("0.01")))
    assert result.quantity == Decimal("1000") / Decimal("101")


def test_full_weight_cannot_spend_more_than_cash() -> None:
    result = execute_signal(BacktestState(Decimal("50"), Decimal("0")), _signal(SignalDirection.LONG), _bar(1), BacktestConfig(Decimal("50")))
    assert result.cash >= 0
    assert result.quantity == Decimal("0.5")


def test_zero_weight_long_closes_position() -> None:
    result = execute_signal(BacktestState(Decimal("0"), Decimal("10")), _signal(SignalDirection.LONG, "0"), _bar(1), BacktestConfig(Decimal("1000")))
    assert result.quantity == Decimal("0")
    assert result.cash == Decimal("1000")
