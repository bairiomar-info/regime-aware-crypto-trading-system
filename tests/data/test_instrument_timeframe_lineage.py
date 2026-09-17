from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from trading_system.data.models.instrument import Instrument, MarketType
from trading_system.data.models.lineage import AssetLineageEvent, LineageConfidence, LineageEventType
from trading_system.data.models.timeframe import Timeframe


def test_instrument_normalizes_identifiers_and_is_spot() -> None:
    instrument = Instrument(symbol="btcusdt", base_asset="btc", quote_asset="usdt", exchange="binance")
    assert instrument.symbol == "BTCUSDT"
    assert instrument.base_asset == "BTC"
    assert instrument.quote_asset == "USDT"
    assert instrument.market_type is MarketType.SPOT


def test_instrument_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Instrument(symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT", exchange="binance", leverage=2)


def test_timeframe_is_closed_enum() -> None:
    assert Timeframe("1h") is Timeframe.H1
    with pytest.raises(ValueError):
        Timeframe("2h")


def test_lineage_requires_relationship() -> None:
    with pytest.raises(ValidationError):
        AssetLineageEvent(event_id="x", event_type=LineageEventType.RENAME, effective_time=datetime(2026,1,1,tzinfo=timezone.utc), source="test", confidence=LineageConfidence.HIGH)


def test_lineage_rejects_self_relationship() -> None:
    with pytest.raises(ValidationError):
        AssetLineageEvent(event_id="x", event_type=LineageEventType.RENAME, effective_time=datetime(2026,1,1,tzinfo=timezone.utc), predecessor_asset_id="BTC", successor_asset_id="btc", source="test", confidence=LineageConfidence.HIGH)


def test_lineage_requires_utc() -> None:
    with pytest.raises(ValidationError):
        AssetLineageEvent(event_id="x", event_type=LineageEventType.RENAME, effective_time=datetime(2026,1,1), predecessor_asset_id="A", successor_asset_id="B", source="test", confidence=LineageConfidence.HIGH)


def test_lineage_normalizes_asset_ids() -> None:
    event = AssetLineageEvent(event_id="rename-1", event_type=LineageEventType.RENAME, effective_time=datetime(2026,1,1,tzinfo=timezone.utc), predecessor_asset_id="old", successor_asset_id="new", conversion_ratio=Decimal("1"), source="test", confidence=LineageConfidence.HIGH)
    assert event.predecessor_asset_id == "OLD"
    assert event.successor_asset_id == "NEW"
