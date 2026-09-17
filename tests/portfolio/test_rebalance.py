from decimal import Decimal

import pytest

from trading_system.portfolio.models import Position, TargetPosition
from trading_system.portfolio.rebalance import calculate_rebalance


def test_rebalance_uses_target_minus_current() -> None:
    result = calculate_rebalance(
        (Position("BTCUSDT", Decimal("2"), Decimal("100")),),
        (TargetPosition("BTCUSDT", Decimal("0.5"), __import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc)),),
        equity=Decimal("1000"), prices={"BTCUSDT": Decimal("100")},
    )
    assert result[0].current_weight == Decimal("0.2")
    assert result[0].delta_weight == Decimal("0.3")


def test_rebalance_rejects_duplicate_positions() -> None:
    with pytest.raises(ValueError, match="duplicate position"):
        calculate_rebalance(
            (Position("BTCUSDT", Decimal("1"), Decimal("100")), Position("BTCUSDT", Decimal("1"), Decimal("100"))),
            (), equity=Decimal("1000"), prices={"BTCUSDT": Decimal("100")},
        )


def test_rebalance_rejects_duplicate_targets() -> None:
    from datetime import datetime, timezone
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="duplicate target"):
        calculate_rebalance(
            (), (TargetPosition("BTCUSDT", Decimal("0.2"), t), TargetPosition("BTCUSDT", Decimal("0.3"), t)),
            equity=Decimal("1000"), prices={},
        )


def test_rebalance_rejects_missing_position_price() -> None:
    with pytest.raises(ValueError, match="missing price"):
        calculate_rebalance(
            (Position("BTCUSDT", Decimal("1"), Decimal("100")),), (), equity=Decimal("1000"), prices={},
        )


def test_rebalance_rejects_aggregate_target_weight_above_one() -> None:
    from datetime import datetime, timezone
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="total portfolio weight"):
        calculate_rebalance(
            (),
            (
                TargetPosition("BTCUSDT", Decimal("0.6"), t),
                TargetPosition("ETHUSDT", Decimal("0.5"), t),
            ),
            equity=Decimal("1000"),
            prices={},
        )


def test_rebalance_accepts_exactly_full_investment() -> None:
    from datetime import datetime, timezone
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = calculate_rebalance(
        (),
        (
            TargetPosition("BTCUSDT", Decimal("0.6"), t),
            TargetPosition("ETHUSDT", Decimal("0.4"), t),
        ),
        equity=Decimal("1000"),
        prices={},
    )
    assert sum(item.target_weight for item in result) == Decimal("1")
