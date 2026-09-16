from datetime import datetime, timezone
from decimal import Decimal

from trading_system.portfolio.models import Position, TargetPosition
from trading_system.portfolio.rebalance import calculate_rebalance


def test_rebalance_calculates_target_minus_current_weight() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = calculate_rebalance(
        (Position("BTCUSDT", Decimal("2"), Decimal("100")),),
        (TargetPosition("BTCUSDT", Decimal("0.3"), now), TargetPosition("ETHUSDT", Decimal("0.2"), now)),
        equity=Decimal("1000"),
        prices={"BTCUSDT": Decimal("100"), "ETHUSDT": Decimal("2000")},
    )
    assert result[0].current_weight == Decimal("0.2")
    assert result[0].delta_weight == Decimal("0.1")
    assert result[1].current_weight == Decimal("0")


def test_missing_price_is_rejected() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    try:
        calculate_rebalance(
            (Position("BTCUSDT", Decimal("1"), Decimal("100")),),
            (TargetPosition("BTCUSDT", Decimal("0.2"), now),),
            equity=Decimal("1000"),
            prices={},
        )
    except ValueError as exc:
        assert "missing price" in str(exc)
    else:
        raise AssertionError("expected ValueError")
