"""Research feature primitives with explicit lookback requirements.

These functions operate only on an already-selected, time-ordered historical
window. The caller owns point-in-time selection; the functions never fetch or
infer future observations.
"""

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation


def simple_return(prices: Iterable[Decimal | str], *, lookback_bars: int) -> Decimal | None:
    """Return cumulative simple price return over ``lookback_bars``.

    The input must contain the current decision-time close as its final value.
    ``None`` is returned when the requested history is unavailable.
    """
    if lookback_bars <= 0:
        raise ValueError("lookback_bars must be positive")
    values = _positive_decimals(prices)
    if len(values) <= lookback_bars:
        return None
    anchor = values[-lookback_bars - 1]
    return values[-1] / anchor - Decimal("1")


def rolling_volatility(
    prices: Iterable[Decimal | str],
    *,
    lookback_bars: int,
    annualization_factor: Decimal | str | None = None,
) -> Decimal | None:
    """Compute realized volatility from close-to-close simple returns.

    Population standard deviation is used for this descriptive feature. The
    annualization factor is optional because the correct factor depends on the
    research decision frequency and must not be hard-coded here.
    """
    if lookback_bars <= 1:
        raise ValueError("lookback_bars must be greater than one")
    values = _positive_decimals(prices)
    if len(values) <= lookback_bars:
        return None

    window = values[-lookback_bars - 1 :]
    returns = [current / previous - Decimal("1") for previous, current in zip(window, window[1:])]
    mean = sum(returns, Decimal("0")) / Decimal(len(returns))
    variance = sum((value - mean) ** 2 for value in returns) / Decimal(len(returns))
    volatility = variance.sqrt()

    if annualization_factor is not None:
        factor = _decimal(annualization_factor)
        if factor <= 0:
            raise ValueError("annualization_factor must be positive")
        volatility *= factor.sqrt()
    return volatility


def ema(prices: Iterable[Decimal | str], *, span: int) -> Decimal | None:
    """Return the exponential moving average at the final observation."""
    if span <= 0:
        raise ValueError("span must be positive")
    values = _positive_decimals(prices)
    if len(values) < span:
        return None

    alpha = Decimal("2") / Decimal(span + 1)
    value = sum(values[:span], Decimal("0")) / Decimal(span)
    for price in values[span:]:
        value = alpha * price + (Decimal("1") - alpha) * value
    return value


def ema_trend_score(
    prices: Iterable[Decimal | str],
    *,
    fast_span: int,
    slow_span: int,
) -> Decimal | None:
    """Measure trend as fast EMA relative to slow EMA minus one.

    Positive values indicate the fast EMA is above the slow EMA. The spans are
    deliberately parameters so their predictive value can be tested rather
    than frozen from the literature.
    """
    if fast_span <= 0 or slow_span <= 0:
        raise ValueError("EMA spans must be positive")
    if fast_span >= slow_span:
        raise ValueError("fast_span must be smaller than slow_span")

    values = _positive_decimals(prices)
    slow = ema(values, span=slow_span)
    fast = ema(values, span=fast_span)
    if slow is None or fast is None:
        return None
    return fast / slow - Decimal("1")


def _positive_decimals(values: Iterable[Decimal | str]) -> list[Decimal]:
    result: list[Decimal] = []
    for value in values:
        try:
            parsed = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError("price must be a valid decimal value") from exc
        if parsed <= 0:
            raise ValueError("price must be positive")
        result.append(parsed)
    return result


def _decimal(value: Decimal | str) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("value must be a valid decimal") from exc
