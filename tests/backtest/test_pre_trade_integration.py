from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar
from trading_system.backtest.integrated import _pre_trade_order, _portfolio_state
from trading_system.compliance.classification import AssetCompliance
from trading_system.execution.gate import PreTradeConfig, validate_pre_trade
from trading_system.portfolio.orders import OrderSide
from trading_system.strategies.models import SignalDirection, StrategySignal


def test_integrated_order_uses_slippage_price() -> None:
    decision = datetime(2026, 1, 1, tzinfo=timezone.utc)
    execution = MarketBar(datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
    signal = StrategySignal(decision, "BTCUSDT", SignalDirection.LONG, "test", target_weight=Decimal("1"))
    order, price = _pre_trade_order(BacktestState(Decimal("100"), Decimal("0")), signal, execution, BacktestConfig(Decimal("100"), slippage_rate=Decimal("0.01")))
    assert order is not None
    assert order.side is OrderSide.BUY
    assert price == Decimal("101")
    assert order.notional == Decimal("100")


def test_pre_trade_rejects_missing_asset_evidence() -> None:
    state = _portfolio_state(BacktestState(Decimal("100"), Decimal("0")), "BTCUSDT")
    from trading_system.portfolio.orders import OrderIntent
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("50"), "test")
    with pytest.raises(ValueError, match="compliance evidence"):
        validate_pre_trade(state, order, Decimal("100"), PreTradeConfig())


def test_pre_trade_rejects_noncompliant_asset() -> None:
    state = _portfolio_state(BacktestState(Decimal("100"), Decimal("0")), "BTCUSDT")
    from trading_system.portfolio.orders import OrderIntent
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("50"), "test")
    evidence = AssetCompliance("BTCUSDT", Decimal("0.06"))
    with pytest.raises(ValueError, match="interest-income"):
        validate_pre_trade(state, order, Decimal("100"), PreTradeConfig(), asset_compliance=evidence)
