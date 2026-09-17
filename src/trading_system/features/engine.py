"""Deterministic, point-in-time market-feature calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from math import log, sqrt
from statistics import mean, pstdev
from typing import Sequence

from trading_system.data.models import Candle

from .models import FeatureSnapshot


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
        """Compute one snapshot using only the supplied endpoint and its history."""
        if not candles:
            raise ValueError("at least one asset series is required")
        series: dict[str, list[Candle]] = {}
        for symbol, values in candles.items():
            ordered = list(values)
            if not ordered:
                continue
            self._validate_series(symbol, ordered)
            series[symbol] = ordered
        if not series:
            raise ValueError("at least one non-empty asset series is required")

        required = self.required_observations
        decision_time = self._validate_alignment(series, min_length=1)
        if len(series) < self.config.min_assets or any(len(values) < required for values in series.values()):
            return FeatureSnapshot(decision_time, None, None, None, None, None, len(series))

        self._validate_alignment(series, min_length=required)
        returns = {symbol: self._log_returns(values) for symbol, values in series.items()}
        trend = self._trend_score(returns)
        volatility = self._realized_volatility(returns)
        latest = {symbol: values[-1] for symbol, values in returns.items()}
        breadth = Decimal(str(sum(value > 0 for value in latest.values()) / len(series)))
        dispersion = Decimal(str(pstdev([float(value) for value in latest.values()])))
        correlation = self._average_pairwise_correlation(returns)
        return FeatureSnapshot(decision_time, trend, volatility, breadth, dispersion, correlation, len(series))

    @property
    def required_observations(self) -> int:
        return max(
            self.config.trend_lookback + 1,
            self.config.volatility_lookback + 1,
            self.config.correlation_lookback + 1,
        )

    def compute_history(self, candles: dict[str, Sequence[Candle]]) -> tuple[FeatureSnapshot, ...]:
        """Produce a causal feature series from the first fully supported endpoint onward."""
        if not candles:
            raise ValueError("at least one asset series is required")
        series = {symbol: list(values) for symbol, values in candles.items() if values}
        if not series:
            return ()
        lengths = {len(values) for values in series.values()}
        if len(lengths) != 1:
            raise ValueError("history computation requires equal-length asset series")
        self._validate_alignment(series, min_length=1)
        for symbol, values in series.items():
            self._validate_series(symbol, values)
        if len(next(iter(series.values()))) < self.required_observations:
            return ()
        snapshots = []
        for end in range(self.required_observations, len(next(iter(series.values()))) + 1):
            prefix = {symbol: tuple(values[:end]) for symbol, values in series.items()}
            snapshots.append(self.compute(prefix))
        return tuple(snapshots)

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
    def _validate_alignment(series: dict[str, list[Candle]], *, min_length: int) -> datetime:
        first = next(iter(series.values()))
        anchor = first[-1]
        for values in series.values():
            last = values[-1]
            if last.open_time != anchor.open_time or last.close_time != anchor.close_time:
                raise ValueError("all asset series must end at the same candle")
            if last.timeframe != anchor.timeframe:
                raise ValueError("all asset series must use the same timeframe")
            if last.instrument.quote_asset != anchor.instrument.quote_asset:
                raise ValueError("all asset series must use the same quote asset")
            if len(values) < min_length:
                raise ValueError("asset series is shorter than the required alignment window")
            window = values[-min_length:]
            anchor_times = [(candle.open_time, candle.close_time) for candle in first[-min_length:]]
            current_times = [(candle.open_time, candle.close_time) for candle in window]
            if current_times != anchor_times:
                raise ValueError("asset histories must be timestamp-aligned over the feature window")
        if anchor.close_time.tzinfo is None or anchor.close_time.utcoffset() != timezone.utc.utcoffset(anchor.close_time):
            raise ValueError("candle times must be UTC")
        return anchor.close_time

    @staticmethod
    def _log_returns(values: Sequence[Candle]) -> list[Decimal]:
        prices = [float(candle.close) for candle in values]
        if any(price <= 0 for price in prices):
            raise ValueError("close prices must be positive")
        return [Decimal(str(log(prices[i] / prices[i - 1]))) for i in range(1, len(prices))]

    def _trend_score(self, returns: dict[str, list[Decimal]]) -> Decimal:
        scores: list[float] = []
        for values in returns.values():
            window = values[-self.config.trend_lookback :]
            cumulative = sum(float(value) for value in window)
            scale = sqrt(sum(float(value) ** 2 for value in window))
            scores.append(cumulative / scale if scale > 0 else 0.0)
        return Decimal(str(mean(scores)))

    def _realized_volatility(self, returns: dict[str, list[Decimal]]) -> Decimal:
        """Return mean per-asset realized volatility, avoiding universe-size scaling."""
        per_asset = []
        for series in returns.values():
            values = [float(value) for value in series[-self.config.volatility_lookback :]]
            per_asset.append(sqrt(sum(value * value for value in values)))
        return Decimal(str(mean(per_asset)))

    def _average_pairwise_correlation(self, returns: dict[str, list[Decimal]]) -> Decimal | None:
        vectors = {
            symbol: [float(value) for value in values[-self.config.correlation_lookback :]]
            for symbol, values in returns.items()
        }
        correlations: list[float] = []
        symbols = sorted(vectors)
        for index, left in enumerate(symbols):
            for right in symbols[index + 1 :]:
                correlation = self._pearson(vectors[left], vectors[right])
                if correlation is None:
                    return None
                correlations.append(correlation)
        return Decimal(str(mean(correlations))) if correlations else None

    @staticmethod
    def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
        if len(left) != len(right) or len(left) < 2:
            raise ValueError("correlation requires aligned histories with at least two returns")
        left_mean = mean(left)
        right_mean = mean(right)
        numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
        left_var = sum((a - left_mean) ** 2 for a in left)
        right_var = sum((b - right_mean) ** 2 for b in right)
        if left_var == 0 or right_var == 0:
            return None
        return numerator / sqrt(left_var * right_var)
