"""Deterministic, point-in-time market-feature calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from math import sqrt
from statistics import mean, pstdev
from typing import Sequence

from trading_system.data.models.candle import Candle

from .models import FeatureSnapshot

getcontext().prec = max(getcontext().prec, 28)


@dataclass(frozen=True)
class FeatureEngineConfig:
    """Research parameters; none are claimed optimal by V1."""

    trend_lookback: int = 20
    volatility_lookback: int = 20
    correlation_lookback: int = 20
    min_assets: int = 3

    def __post_init__(self) -> None:
        for name in ("trend_lookback", "volatility_lookback", "correlation_lookback"):
            if getattr(self, name) < 2:
                raise ValueError(f"{name} must be at least 2")
        if self.min_assets < 2:
            raise ValueError("min_assets must be at least 2")


class FeatureEngine:
    """Compute causal market features from finalized, aligned candles.

    The engine never fetches data and never looks beyond the last supplied candle.
    Callers must provide candles in chronological order and must exclude any
    unfinalized candle from research input.
    """

    def __init__(self, config: FeatureEngineConfig | None = None) -> None:
        self.config = config or FeatureEngineConfig()

    def compute(self, candles: dict[str, Sequence[Candle]]) -> FeatureSnapshot:
        if not candles:
            raise ValueError("at least one asset series is required")

        series: dict[str, list[Candle]] = {}
        for symbol, values in candles.items():
            ordered = list(values)
            if not ordered:
                continue
            self._validate_series(symbol, ordered)
            if ordered[-1].is_closed is not True:
                raise ValueError("feature input must end on a finalized candle")
            series[symbol] = ordered

        if not series:
            raise ValueError("at least one non-empty asset series is required")
        decision_time = self._validate_alignment(series)
        usable = {
            symbol: values
            for symbol, values in series.items()
            if len(values) >= max(self.config.trend_lookback + 1, self.config.volatility_lookback + 1, self.config.correlation_lookback + 1)
        }
        asset_count = len(usable)
        if asset_count < self.config.min_assets:
            return FeatureSnapshot(decision_time, None, None, None, None, None, asset_count)

        returns = {symbol: self._log_returns(values) for symbol, values in usable.items()}
        trend = self._trend_score(returns)
        volatility = self._realized_volatility(returns)
        latest = {symbol: values[-1] for symbol, values in returns.items()}
        breadth = Decimal(str(sum(value > 0 for value in latest.values()) / asset_count))
        dispersion = Decimal(str(pstdev([float(value) for value in latest.values()]))) if asset_count >= 2 else None
        correlation = self._average_pairwise_correlation(returns)
        return FeatureSnapshot(decision_time, trend, volatility, breadth, dispersion, correlation, asset_count)

    @staticmethod
    def _validate_series(symbol: str, values: list[Candle]) -> None:
        previous: Candle | None = None
        for candle in values:
            if candle.instrument.symbol != symbol.upper():
                raise ValueError("series key must match candle instrument symbol")
            if candle.is_closed is not True:
                raise ValueError("feature input must contain finalized candles only")
            if previous is not None:
                if candle.timeframe != previous.timeframe:
                    raise ValueError("all candles in a series must use one timeframe")
                if candle.open_time <= previous.open_time:
                    raise ValueError("candles must be strictly chronological")
            previous = candle

    @staticmethod
    def _validate_alignment(series: dict[str, list[Candle]]) -> datetime:
        first = next(iter(series.values()))[-1]
        for values in series.values():
            last = values[-1]
            if last.open_time != first.open_time or last.close_time != first.close_time:
                raise ValueError("all asset series must end at the same candle")
            if last.timeframe != first.timeframe:
                raise ValueError("all asset series must use the same timeframe")
            if last.instrument.quote_asset != first.instrument.quote_asset:
                raise ValueError("all asset series must use the same quote asset")
        if first.close_time.tzinfo is None or first.close_time.utcoffset() != timezone.utc.utcoffset(first.close_time):
            raise ValueError("candle times must be UTC")
        return first.close_time

    @staticmethod
    def _log_returns(values: Sequence[Candle]) -> list[Decimal]:
        prices = [float(candle.close) for candle in values]
        if any(price <= 0 for price in prices):
            raise ValueError("close prices must be positive")
        return [Decimal(str(__import__("math").log(prices[i] / prices[i - 1]))) for i in range(1, len(prices))]

    def _trend_score(self, returns: dict[str, list[Decimal]]) -> Decimal:
        lookback = self.config.trend_lookback
        scores: list[float] = []
        for values in returns.values():
            window = values[-lookback:]
            cumulative = sum(float(value) for value in window)
            scale = sqrt(sum(float(value) ** 2 for value in window))
            scores.append(cumulative / scale if scale > 0 else 0.0)
        return Decimal(str(mean(scores)))

    def _realized_volatility(self, returns: dict[str, list[Decimal]]) -> Decimal:
        window = self.config.volatility_lookback
        values = [float(value) for series in returns.values() for value in series[-window:]]
        return Decimal(str(sqrt(sum(value * value for value in values))))

    def _average_pairwise_correlation(self, returns: dict[str, list[Decimal]]) -> Decimal:
        window = self.config.correlation_lookback
        vectors = {symbol: [float(value) for value in values[-window:]] for symbol, values in returns.items()}
        correlations: list[float] = []
        symbols = sorted(vectors)
        for index, left in enumerate(symbols):
            for right in symbols[index + 1 :]:
                correlations.append(self._pearson(vectors[left], vectors[right]))
        if not correlations:
            return Decimal("0")
        return Decimal(str(mean(correlations)))

    @staticmethod
    def _pearson(left: Sequence[float], right: Sequence[float]) -> float:
        if len(left) != len(right) or len(left) < 2:
            raise ValueError("correlation requires aligned histories with at least two returns")
        left_mean = mean(left)
        right_mean = mean(right)
        numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
        left_var = sum((a - left_mean) ** 2 for a in left)
        right_var = sum((b - right_mean) ** 2 for b in right)
        if left_var == 0 or right_var == 0:
            return 0.0
        return numerator / sqrt(left_var * right_var)
