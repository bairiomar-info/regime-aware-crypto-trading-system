from datetime import datetime, timedelta, timezone
from decimal import Decimal

from trading_system.data.models import Candle, Instrument, Timeframe
from trading_system.data.validation import (
    AnomalySeverity,
    RecordValidator,
    SequenceValidator,
    ValidationStatus,
)


UTC = timezone.utc


def make_candle(open_time: datetime, *, is_closed: bool = True) -> Candle:
    instrument = Instrument(
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        exchange="BINANCE",
    )
    return Candle(
        instrument=instrument,
        timeframe=Timeframe.M1,
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
        volume=Decimal("2"),
        quote_volume=Decimal("210"),
        trade_count=10,
        taker_buy_base_volume=Decimal("1"),
        taker_buy_quote_volume=Decimal("105"),
        source="binance",
        is_closed=is_closed,
    )


def test_record_validator_flags_forming_candle():
    candle = make_candle(datetime(2026, 9, 1, 10, 0, tzinfo=UTC), is_closed=False)

    anomalies = RecordValidator().validate(candle)

    assert len(anomalies) == 1
    assert anomalies[0].code == "FORMING_CANDLE"
    assert anomalies[0].severity == AnomalySeverity.WARNING


def test_sequence_validator_passes_continuous_closed_candles():
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    candles = [make_candle(start + timedelta(minutes=i)) for i in range(3)]

    report = SequenceValidator().validate(candles)

    assert report.status == ValidationStatus.PASS
    assert report.records_checked == 3
    assert report.valid_records == 3
    assert report.invalid_records == 0
    assert report.gap_count == 0
    assert report.duplicate_count == 0
    assert report.out_of_order_count == 0


def test_sequence_validator_reports_gap_without_repairing_data():
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    candles = [make_candle(start), make_candle(start + timedelta(minutes=2))]

    report = SequenceValidator().validate(candles)

    assert report.status == ValidationStatus.WARNING
    assert report.gap_count == 1
    assert report.invalid_records == 0
    assert [c.open_time for c in candles] == [start, start + timedelta(minutes=2)]
    assert report.anomalies[-1].code == "MISSING_INTERVAL"


def test_sequence_validator_reports_duplicate():
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    candle = make_candle(start)

    report = SequenceValidator().validate([candle, candle])

    assert report.status == ValidationStatus.FAIL
    assert report.duplicate_count == 1
    assert report.invalid_records == 1
    assert any(a.code == "DUPLICATE_CANDLE" for a in report.anomalies)


def test_sequence_validator_reports_out_of_order():
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    candles = [make_candle(start), make_candle(start + timedelta(minutes=2)), make_candle(start + timedelta(minutes=1))]

    report = SequenceValidator().validate(candles)

    assert report.status == ValidationStatus.FAIL
    assert report.out_of_order_count == 1
    assert report.invalid_records == 1
    assert any(a.code == "OUT_OF_ORDER" for a in report.anomalies)


def test_sequence_validator_reports_forming_candle_as_warning():
    start = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    candles = [make_candle(start), make_candle(start + timedelta(minutes=1), is_closed=False)]

    report = SequenceValidator().validate(candles)

    assert report.status == ValidationStatus.WARNING
    assert report.invalid_records == 0
    assert any(a.code == "FORMING_CANDLE" for a in report.anomalies)
