import pytest
from pydantic import ValidationError

from trading_system.core.config import SystemConfig


def test_default_configuration_is_long_only_spot_and_shariah_compliant():
    config = SystemConfig()

    assert config.long_only is True
    assert config.spot_only is True
    assert config.shariah_compliant is True
    assert config.initial_capital == 1000.0


def test_initial_capital_must_be_positive():
    with pytest.raises(ValidationError):
        SystemConfig(initial_capital=0)


def test_unknown_configuration_fields_are_rejected():
    with pytest.raises(ValidationError):
        SystemConfig(unknown_setting=True)
