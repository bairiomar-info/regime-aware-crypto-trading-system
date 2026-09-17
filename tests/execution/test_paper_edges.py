from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.compliance.classification import AssetCompliance
from trading_system.execution.paper import PaperFill, execute_paper_order
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import PortfolioState

T = datetime(2026, 1, 1, tzinfo=timezone.utc)
ORDER = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("100"), "test")
STATE = PortfolioState(Decimal("1000"), ())


@pytest.mark.parametrize("price", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_paper_fill_rejects_invalid_fill_price(price: Decimal) -> None:
    with pytest.raises(ValueError, match="fill_price"):
        PaperFill(T, ORDER, price, Decimal("0"))


@pytest.mark.parametrize("fee", [Decimal("-0.01"), Decimal("1"), Decimal("NaN"), Decimal("Infinity")])
def test_paper_fill_rejects_invalid_fee_rate(fee: Decimal) -> None:
    with pytest.raises(ValueError, match="fee_rate"):
        PaperFill(T, ORDER, Decimal("100"), fee)


def test_paper_execution_rejects_non_compliant_asset() -> None:
    with pytest.raises(ValueError, match="interest-income"):
        execute_paper_order(
            STATE, ORDER, timestamp=T, market_price=Decimal("100"), fill_price=Decimal("100"),
            fee_rate=Decimal("0"), asset_compliance=AssetCompliance("BTCUSDT", Decimal("0.06")),
        )


def test_paper_execution_rejects_gambling_like_asset() -> None:
    with pytest.raises(ValueError, match="gambling-like"):
        execute_paper_order(
            STATE, ORDER, timestamp=T, market_price=Decimal("100"), fill_price=Decimal("100"),
            fee_rate=Decimal("0"), asset_compliance=AssetCompliance("BTCUSDT", Decimal("0"), gambling_like=True),
        )


def test_paper_execution_rejects_invalid_timestamp() -> None:
    with pytest.raises(ValueError, match="UTC"):
        execute_paper_order(
            STATE, ORDER, timestamp=datetime(2026, 1, 1), market_price=Decimal("100"), fill_price=Decimal("100"),
            fee_rate=Decimal("0"), asset_compliance=AssetCompliance("BTCUSDT", Decimal("0")),
        )
