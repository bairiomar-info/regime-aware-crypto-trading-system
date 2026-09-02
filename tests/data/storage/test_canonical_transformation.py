from datetime import UTC, datetime
from decimal import Decimal

import pytest

from trading_system.data.models import Candle, Instrument, Timeframe
from trading_system.data.storage.canonical import (
    CanonicalizationContract,
    CanonicalizationError,
    QualityClassification,
    canonicalize_candles,
)


CONTRACT = CanonicalizationContract(
    contract_version="1.0.0",
    schema_version="1.0.0",
    normalization_version="1.0.0",
    validation_version="1.0.0",
)


def make_candle(minute: int, *, close: str = "101", is_closed: bool = True) -> Candle:
    return Candle(
        instrument=Instrument(
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            exchange="BINANCE",
        ),
        timeframe=Timeframe.M1,
        open_time=datetime(2026, 1, 1, 0, minute, tzinfo=UTC),
        close_time=datetime(2026, 1, 1, 0, minute, 59, 999000, tzinfo=UTC),
        open=Decimal("100"),
        high=Decimal("102"),
        low=Decimal("99"),
        close=Decimal(close),
        volume=Decimal("10.12345678"),
        quote_volume=Decimal("1012.345678"),
        trade_count=10,
        taker_buy_base_volume=Decimal("5"),
        taker_buy_quote_volume=Decimal("500"),
        source="binance",
        is_closed=is_closed,
    )


def test_transformation_is_deterministically_sorted():
    result = canonicalize_candles(
        [make_candle(2), make_candle(0), make_candle(1)], contract=CONTRACT
    )

    assert [c.open_time.minute for c in result.candles] == [0, 1, 2]
    assert result.diagnostics == ()


def test_identical_duplicates_are_removed_and_diagnosed():
    candle = make_candle(0)
    result = canonicalize_candles([candle, candle], contract=CONTRACT)

    assert len(result.candles) == 1
    assert [d.classification for d in result.diagnostics] == [QualityClassification.DUPLICATE]


def test_conflicting_duplicates_are_rejected():
    with pytest.raises(CanonicalizationError):
        canonicalize_candles(
            [make_candle(0, close="101"), make_candle(0, close="102")],
            contract=CONTRACT,
        )


def test_incomplete_candle_is_excluded_when_contract_requires_closed():
    result = canonicalize_candles([make_candle(0, is_closed=False)], contract=CONTRACT)

    assert result.candles == ()
    assert result.diagnostics[0].classification == QualityClassification.UNKNOWN_GAP


def test_missing_interval_is_diagnosed_without_fabrication():
    result = canonicalize_candles([make_candle(0), make_candle(2)], contract=CONTRACT)

    assert [c.open_time.minute for c in result.candles] == [0, 2]
    assert [d.classification for d in result.diagnostics] == [QualityClassification.DATA_GAP]
    assert result.diagnostics[0].observed_at.minute == 1


def test_non_rejecting_conflict_keeps_first_deterministically():
    contract = CONTRACT.model_copy(update={"reject_conflicting_duplicates": False})
    result = canonicalize_candles(
        [make_candle(0, close="101"), make_candle(0, close="102")],
        contract=contract,
    )

    assert len(result.candles) == 1
    assert result.candles[0].close == Decimal("101")
    assert [d.classification for d in result.diagnostics] == [QualityClassification.DATA_CONFLICT]
