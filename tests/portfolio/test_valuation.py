from decimal import Decimal

from trading_system.portfolio.models import Position
from trading_system.portfolio.valuation import portfolio_market_value, position_value


def test_position_and_portfolio_value() -> None:
    positions = (
        Position("BTCUSDT", Decimal("2"), Decimal("100")),
        Position("ETHUSDT", Decimal("3"), Decimal("50")),
    )
    assert position_value(positions[0], Decimal("120")) == Decimal("240")
    assert portfolio_market_value(positions, {"BTCUSDT": Decimal("120"), "ETHUSDT": Decimal("60")}) == Decimal("420")
