from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def signal(weight: str, decision_hour: int = 0) -> StrategySignal:
    return StrategySignal(datetime(2026, 9, 16, decision_hour, tzinfo=timezone.utc), "BTCUSDT", SignalDirection.LONG, "cost test", Decimal(weight))


def bar(hour: int = 1, price: str = "100") -> MarketBar:
    return MarketBar(datetime(2026, 9, 16, hour, tzinfo=timezone.utc), Decimal(price), Decimal(price))


def test_long_execution_applies_fee_and_slippage() -> None:
    state = execute_signal(BacktestState(Decimal("1000"), Decimal("0")), signal("1"), bar(), BacktestConfig(Decimal("1000"), fee_rate=Decimal("0.01"), slippage_rate=Decimal("0.01")))
    expected_price = Decimal("101")
    expected_quantity = Decimal("1000") / (expected_price * Decimal("1.01"))
    assert state.quantity == expected_quantity
    assert state.cash >= 0


def test_buy_slippage_reduces_filled_quantity() -> None:
    plain = execute_signal(BacktestState(Decimal("1000"), Decimal("0")), signal("1"), bar(), BacktestConfig(Decimal("1000")))
    slipped = execute_signal(BacktestState(Decimal("1000"), Decimal("0")), signal("1"), bar(), BacktestConfig(Decimal("1000"), slippage_rate=Decimal("0.1")))
    assert slipped.quantity < plain.quantity


def test_sell_slippage_reduces_proceeds() -> None:
    plain = execute_signal(BacktestState(Decimal("0"), Decimal("10")), signal("0.1"), bar(), BacktestConfig(Decimal("1000")))
    slipped = execute_signal(BacktestState(Decimal("0"), Decimal("10")), signal("0.1"), bar(), BacktestConfig(Decimal("1000"), slippage_rate=Decimal("0.1")))
    assert slipped.cash < plain.cash


def test_cost_rates_are_rejected_at_one_or_above() -> None:
    for fee, slip in ((Decimal("1"), Decimal("0")), (Decimal("0"), Decimal("1")), (Decimal("2"), Decimal("0"))):
        with pytest.raises(ValueError):
            BacktestConfig(Decimal("1000"), fee_rate=fee, slippage_rate=slip)


def test_cost_rates_reject_non_finite_and_negative_values() -> None:
    for fee, slip in ((Decimal("NaN"), Decimal("0")), (Decimal("0"), Decimal("NaN")), (Decimal("-0.1"), Decimal("0"))):
        with pytest.raises(ValueError):
            BacktestConfig(Decimal("1000"), fee_rate=fee, slippage_rate=slip)
