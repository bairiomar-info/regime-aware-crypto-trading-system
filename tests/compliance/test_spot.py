import pytest

from trading_system.compliance.spot import validate_spot_symbol


def test_forbidden_symbol_is_blocked() -> None:
    with pytest.raises(ValueError, match="blocked"):
        validate_spot_symbol("USDT")


def test_normal_symbol_is_allowed() -> None:
    validate_spot_symbol("BTCUSDT")
