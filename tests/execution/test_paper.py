from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.compliance.classification import AssetCompliance
from trading_system.execution.paper import execute_paper_order
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import AssetBalance, PortfolioState


COMPLIANT_BTC = AssetCompliance("BTCUSDT", Decimal("0.01"))


def test_paper_execution_returns_fill_and_updated_state() -> None:
    state = PortfolioState(cash=Decimal("1000"), balances=())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    result = execute_paper_order(state, order, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), market_price=Decimal("100"), fill_price=Decimal("100"), fee_rate=Decimal("0"), asset_compliance=COMPLIANT_BTC)
    assert result.fill.order == order
    assert result.fill.fill_price == Decimal("100")
    assert result.state.cash == Decimal("900")
    assert result.state.balances[0].quantity == Decimal("1")


def test_paper_execution_requires_compliance_evidence() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError, match="evidence"):
        execute_paper_order(state, order, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), market_price=Decimal("100"), fill_price=Decimal("100"), fee_rate=Decimal("0"))


def test_paper_execution_rejects_non_utc_timestamp() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
    with pytest.raises(ValueError):
        execute_paper_order(state, order, timestamp=datetime(2026, 1, 1), market_price=Decimal("100"), fill_price=Decimal("100"), fee_rate=Decimal("0"), asset_compliance=COMPLIANT_BTC)


def test_paper_execution_rejects_oversell_before_state_change() -> None:
    state = PortfolioState(Decimal("1000"), (AssetBalance("BTCUSDT", Decimal("1")),))
    order = OrderIntent("BTCUSDT", OrderSide.SELL, Decimal("200"), "test")
    with pytest.raises(ValueError, match="available spot position"):
        execute_paper_order(state, order, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), market_price=Decimal("100"), fill_price=Decimal("100"), fee_rate=Decimal("0"), asset_compliance=COMPLIANT_BTC)
