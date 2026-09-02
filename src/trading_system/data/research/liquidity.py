"""Point-in-time market-universe liquidity measurements."""

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from statistics import median


def rolling_quote_volume(
    quote_volumes: Iterable[Decimal | str | None],
    *,
    lookback_bars: int,
    minimum_quote_volume: Decimal | str | None = None,
    minimum_coverage: Decimal | str = Decimal("1"),
) -> tuple[Decimal | None, Decimal, bool]:
    """Measure typical quote volume from observations available as-of T.

    ``quote_volumes`` represents one already-selected historical lookback window.
    The decision timestamp is therefore owned by the caller, preventing this
    low-level calculation from accidentally reaching into future observations.
    """
    if lookback_bars <= 0:
        raise ValueError("lookback_bars must be positive")
    coverage = _decimal(minimum_coverage)
    if coverage < 0 or coverage > 1:
        raise ValueError("minimum_coverage must be between 0 and 1")

    values: list[Decimal] = []
    for value in quote_volumes:
        if value is None:
            continue
        try:
            parsed = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError("quote volume must be a valid decimal value") from exc
        if parsed < 0:
            raise ValueError("quote volume cannot be negative")
        values.append(parsed)

    if len(values) > lookback_bars:
        values = values[-lookback_bars:]
    coverage_ratio = Decimal(len(values)) / Decimal(lookback_bars)
    if not values or coverage_ratio < coverage:
        return None, coverage_ratio, False

    typical = Decimal(str(median(values)))
    threshold = None if minimum_quote_volume is None else _decimal(minimum_quote_volume)
    sufficient = threshold is None or typical >= threshold
    return typical, coverage_ratio, sufficient


def _decimal(value: Decimal | str) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("value must be a valid decimal") from exc
    if result < 0:
        raise ValueError("value cannot be negative")
    return result
