import pytest

from trading_system.data.models import Timeframe


def test_supported_timeframes_are_explicit():
    assert [timeframe.value for timeframe in Timeframe] == [
        "1m",
        "5m",
        "15m",
        "1h",
        "4h",
        "1d",
    ]


def test_unknown_timeframe_is_rejected():
    with pytest.raises(ValueError):
        Timeframe("2m")
