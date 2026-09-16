"""Adapt canonical Candle models to the causal backtest bar contract."""

from __future__ import annotations

from collections.abc import Sequence

from trading_system.data.models import Candle

from .engine import MarketBar


def candles_to_market_bars(candles: Sequence[Candle]) -> tuple[MarketBar, ...]:
    """Convert validated canonical candles into chronological backtest bars."""
    if not candles:
        raise ValueError("candles must not be empty")
    bars = tuple(
        MarketBar(timestamp=candle.open_time, open=candle.open, close=candle.close)
        for candle in candles
    )
    for previous, current in zip(bars, bars[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("candles must be strictly chronological")
    return bars
