from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from trading_system.data.acquisition.manifest import AcquisitionManifest
from trading_system.data.acquisition.service import AcquisitionDataQualityError, acquire_to_parquet
from trading_system.data.models import Candle, Instrument, MarketType, Timeframe
from trading_system.data.storage.parquet import read_candles

INSTRUMENT = Instrument(symbol="BTCUSDT", base_asset="BTC", quote_asset="USDT", market_type=MarketType.SPOT, exchange="BINANCE")
START = datetime(2026, 1, 1, tzinfo=UTC)

def candle(i=0, closed=True):
    t = START + timedelta(hours=i)
    return Candle(instrument=INSTRUMENT, timeframe=Timeframe.H1, open_time=t, close_time=t+timedelta(minutes=59),
        open=Decimal("100"), high=Decimal("110"), low=Decimal("90"), close=Decimal("105"),
        volume=Decimal("10"), quote_volume=Decimal("1000"), trade_count=10,
        taker_buy_base_volume=Decimal("5"), taker_buy_quote_volume=Decimal("500"), source="binance", is_closed=closed)

class Provider:
    def __init__(self, rows): self.rows = rows
    def fetch(self, **kwargs): return self.rows

def test_service_persists_and_returns_manifest(tmp_path):
    manifest = acquire_to_parquet(provider=Provider([candle(0), candle(1)]), instrument=INSTRUMENT, timeframe=Timeframe.H1,
        start=START, end=START+timedelta(hours=2), destination=tmp_path/"btc.parquet")
    assert isinstance(manifest, AcquisitionManifest)
    assert manifest.status == "complete"
    assert manifest.candle_count == 2
    assert len(read_candles(tmp_path/"btc.parquet")) == 2

def test_duplicate_identical_candle_is_deduplicated(tmp_path):
    manifest = acquire_to_parquet(provider=Provider([candle(0), candle(0), candle(1)]), instrument=INSTRUMENT, timeframe=Timeframe.H1,
        start=START, end=START+timedelta(hours=2), destination=tmp_path/"btc.parquet")
    assert manifest.duplicate_count == 1
    assert manifest.candle_count == 2

def test_conflicting_duplicate_is_rejected(tmp_path):
    altered = candle(0).model_copy(update={"close": Decimal("106")})
    with pytest.raises(AcquisitionDataQualityError, match="conflicting duplicate"):
        acquire_to_parquet(provider=Provider([candle(0), altered]), instrument=INSTRUMENT, timeframe=Timeframe.H1,
            start=START, end=START+timedelta(hours=2), destination=tmp_path/"btc.parquet")

def test_gap_is_rejected(tmp_path):
    with pytest.raises(AcquisitionDataQualityError, match="interval gaps"):
        acquire_to_parquet(provider=Provider([candle(0), candle(2)]), instrument=INSTRUMENT, timeframe=Timeframe.H1,
            start=START, end=START+timedelta(hours=3), destination=tmp_path/"btc.parquet")

def test_incomplete_candle_is_not_persisted_and_marks_partial(tmp_path):
    manifest = acquire_to_parquet(provider=Provider([candle(0), candle(1, closed=False)]), instrument=INSTRUMENT, timeframe=Timeframe.H1,
        start=START, end=START+timedelta(hours=2), destination=tmp_path/"btc.parquet")
    assert manifest.status == "partial"
    assert manifest.candle_count == 1
    assert len(read_candles(tmp_path/"btc.parquet")) == 1
