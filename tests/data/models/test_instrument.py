import pytest
from pydantic import ValidationError

from trading_system.data.models import Instrument, MarketType


def test_instrument_normalizes_identifiers_and_defaults_to_spot():
    instrument = Instrument(
        symbol="btcusdt",
        base_asset="btc",
        quote_asset="usdt",
        exchange="binance",
    )

    assert instrument.symbol == "BTCUSDT"
    assert instrument.base_asset == "BTC"
    assert instrument.quote_asset == "USDT"
    assert instrument.exchange == "BINANCE"
    assert instrument.market_type is MarketType.SPOT


def test_instrument_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        Instrument(
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            exchange="BINANCE",
            leverage=2,
        )
