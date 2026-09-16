from decimal import Decimal

import pytest

from trading_system.portfolio.constraints import validate_target_weights


def test_target_weights_cannot_exceed_total_constraint() -> None:
    with pytest.raises(ValueError, match="exceed"):
        validate_target_weights((("BTCUSDT", Decimal("0.7")), ("ETHUSDT", Decimal("0.4"))))
