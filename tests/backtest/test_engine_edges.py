from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def bar(hour: int, open_price: str = "100", close: str = "100") -> MarketBar:
    return MarketBar(datetime(2026, 1, 1, hour, tzinfo=timezone.utc), Decimal(open_price), Decimal(close))


def signal(hour: int, direction: SignalDirection = SignalDirection.LONG, weight: str | None = "1") -> StrategySignal:
    return StrategySignal(
        datetime(2026, 1, 1, hour, tzinfo=timezone.utc),
        "BTCUSDT",
        direction,
        "test",
        target_weight=Decimal(weight) if weight is not None else None,
    )


@pytest.mark.parametrize("cash", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_backtest_config_rejects_invalid_initial_cash(cash: Decimal) -> None:
    with pytest.raises(ValueError, match="initial_cash"):
        BacktestConfig(cash)


@pytest.mark.parametrize("field", ["fee_rate", "slippage_rate"])
def test_backtest_config_rejects_negative_rates(field: str) -> None:
    values = {"initial_cash": Decimal("1000"), "fee_rate": Decimal("0"), "slippage_rate": Decimal("0")}
    values[field] = Decimal("-0.01")
    with pytest.raises(ValueError, match="rates non-negative"):
        BacktestConfig(**values)


@pytest.mark.parametrize("field", ["fee_rate", "slippage_rate"])
def test_backtest_config_rejects_rate_at_one(field: str) -> None:
    values = {"initial_cash": Decimal("1000"), "fee_rate": Decimal("0"), "slippage_rate": Decimal("0")}
    values[field] = Decimal("1")
    with pytest.raises(ValueError, match="below 1"):
        BacktestConfig(**values)


@pytest.mark.parametrize("value_name", ["open", "close"])
def test_market_bar_rejects_non_positive_prices(value_name: str) -> None:
    values = {"open_price": "100", "close": "100"}
    values["open_price" if value_name == "open" else "close"] = "0"
    with pytest.raises(ValueError, match=value_name):
        bar(0, **values)


def test_market_bar_requires_utc_timestamp() -> None:
    with pytest.raises(ValueError, match="bar timestamp"):
        MarketBar(datetime(2026, 1, 1), Decimal("100"), Decimal("100"))


def test_execute_signal_rejects_same_timestamp_execution() -> None:
    with pytest.raises(ValueError, match="strictly after"):
        execute_signal(BacktestState(Decimal("1000"), Decimal("0")), signal(1), bar(1), BacktestConfig(Decimal("1000")))


def test_execute_signal_rejects_execution_before_decision() -> None:
    with pytest.raises(ValueError, match="strictly after"):
        execute_signal(BacktestState(Decimal("1000"), Decimal("0")), signal(2), bar(1), BacktestConfig(Decimal("1000")))


def test_no_trade_signal_preserves_state_exactly() -> None:
    state = BacktestState(Decimal("321.5"), Decimal("2.5"))
    result = execute_signal(state, signal(0, SignalDirection.NO_TRADE, None), bar(1), BacktestConfig(Decimal("1000")))
    assert result == state


def test_long_without_target_weight_is_rejected() -> None:
    with pytest.raises(ValueError, match="target_weight"):
        execute_signal(BacktestState(Decimal("1000"), Decimal("0")), signal(0, SignalDirection.LONG, None), bar(1), BacktestConfig(Decimal("1000")))


def test_non_long_direction_is_rejected() -> None:
    fake_direction = object()
    invalid_signal = StrategySignal(
        datetime(2026, 1, 1, tzinfo=timezone.utc), "BTCUSDT", fake_direction, "test", target_weight=Decimal("1")  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="only LONG"):
        execute_signal(BacktestState(Decimal("1000"), Decimal("0")), invalid_signal, bar(1), BacktestConfig(Decimal("1000")))


def test_slippage_increases_buy_execution_cost() -> None:
    result = execute_signal(
        BacktestState(Decimal("1000"), Decimal("0")), signal(0), bar(1, "100"),
        BacktestConfig(Decimal("1000"), slippage_rate=Decimal("0.01")),
    )
    assert result.quantity == Decimal("1000") / Decimal("101")
    assert result.cash == Decimal("0")


def test_fee_reduces_cash_after_buy() -> None:
    result = execute_signal(
        BacktestState(Decimal("1000"), Decimal("0")), signal(0), bar(1, "100"),
        BacktestConfig(Decimal("1000"), fee_rate=Decimal("0.01")),
    )
    assert result.quantity == Decimal("1000") / Decimal("101")
    assert result.cash == Decimal("0")


def test_partial_target_weight_leaves_cash_uninvested() -> None:
    result = execute_signal(
        BacktestState(Decimal("1000"), Decimal("0")), signal(0, SignalDirection.LONG, "0.5"), bar(1, "100"),
        BacktestConfig(Decimal("1000")),
    )
    assert result.quantity == Decimal("5")
    assert result.cash == Decimal("500")
