from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def _signal(weight: str = "1") -> StrategySignal:
    return StrategySignal(
        datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
        "BTCUSDT",
        SignalDirection.LONG,
        "test",
        target_weight=Decimal(weight),
    )


def _bar(open_price: str = "100", hour: int = 13) -> MarketBar:
    return MarketBar(datetime(2026, 1, 1, hour, tzinfo=timezone.utc), Decimal(open_price), Decimal(open_price))


def test_execution_is_strictly_after_decision() -> None:
    state = BacktestState(Decimal("1000"), Decimal("0"))
    with pytest.raises(ValueError, match="strictly after"):
        execute_signal(state, _signal(), _bar(hour=12), BacktestConfig(Decimal("1000")))


def test_buy_slippage_and_fee_are_applied_deterministically() -> None:
    state = BacktestState(Decimal("1000"), Decimal("0"))
    config = BacktestConfig(Decimal("1000"), fee_rate=Decimal("0.01"), slippage_rate=Decimal("0.01"))
    result = execute_signal(state, _signal(), _bar(), config)
    assert result.quantity == Decimal("1000") / (Decimal("101") * Decimal("1.01"))
    assert result.cash == Decimal("0")


def test_sell_uses_adverse_slippage_and_fee() -> None:
    state = BacktestState(Decimal("0"), Decimal("10"))
    config = BacktestConfig(Decimal("1000"), fee_rate=Decimal("0.01"), slippage_rate=Decimal("0.02"))
    result = execute_signal(state, _signal("0.1"), _bar(), config)
    assert result.quantity < Decimal("10")
    assert result.cash > Decimal("0")


def test_no_trade_does_not_change_state() -> None:
    t = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    signal = StrategySignal(t, "BTCUSDT", SignalDirection.NO_TRADE, "test")
    state = BacktestState(Decimal("1000"), Decimal("2"))
    assert execute_signal(state, signal, _bar(), BacktestConfig(Decimal("1000"))) == state


def test_invalid_bar_price_is_rejected() -> None:
    with pytest.raises(ValueError):
        MarketBar(datetime(2026, 1, 1, 13, tzinfo=timezone.utc), Decimal("0"), Decimal("100"))


def test_invalid_backtest_rates_are_rejected() -> None:
    for fee, slip in ((Decimal("1"), Decimal("0")), (Decimal("0"), Decimal("1")), (Decimal("NaN"), Decimal("0"))):
        with pytest.raises(ValueError):
            BacktestConfig(Decimal("1000"), fee_rate=fee, slippage_rate=slip)
