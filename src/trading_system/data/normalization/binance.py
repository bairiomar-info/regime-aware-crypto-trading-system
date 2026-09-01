"""Pure normalization for Binance Spot REST kline payloads."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from ..models import Candle, Instrument, Timeframe


@dataclass(frozen=True)
class BinanceRawKline:
    """Typed representation of a Binance REST kline row."""

    open_time_ms: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time_ms: int
    quote_volume: str
    trade_count: int
    taker_buy_base_volume: str
    taker_buy_quote_volume: str


class BinanceKlineNormalizer:
    """Convert one Binance kline into the canonical Candle model."""

    def normalize(
        self,
        raw: BinanceRawKline,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        is_closed: bool = True,
    ) -> Candle:
        open_time = self._milliseconds_to_utc(raw.open_time_ms)
        close_time = self._milliseconds_to_utc(raw.close_time_ms)

        return Candle(
            instrument=instrument,
            timeframe=timeframe,
            open_time=open_time,
            close_time=close_time,
            open=Decimal(raw.open),
            high=Decimal(raw.high),
            low=Decimal(raw.low),
            close=Decimal(raw.close),
            volume=Decimal(raw.volume),
            quote_volume=Decimal(raw.quote_volume),
            trade_count=raw.trade_count,
            taker_buy_base_volume=Decimal(raw.taker_buy_base_volume),
            taker_buy_quote_volume=Decimal(raw.taker_buy_quote_volume),
            source="binance",
            is_closed=is_closed,
        )

    @staticmethod
    def _milliseconds_to_utc(value: int) -> datetime:
        if not isinstance(value, int) or value < 0:
            raise ValueError("Binance millisecond timestamp must be a non-negative integer")
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
