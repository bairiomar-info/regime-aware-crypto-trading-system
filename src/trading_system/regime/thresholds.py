"""Past-only empirical threshold helpers for regime classification."""

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation


def empirical_quantile(values: Sequence[Decimal | str], quantile: Decimal | str) -> Decimal | None:
    """Return a deterministic linearly interpolated empirical quantile.

    The caller must provide a point-in-time historical window. This helper does
    not fetch data or impose a research-optimal window/quantile.
    """
    if not 0 <= Decimal(str(quantile)) <= 1:
        raise ValueError("quantile must be between zero and one")
    parsed = sorted(_decimal(v) for v in values)
    if not parsed:
        return None
    q = Decimal(str(quantile))
    if len(parsed) == 1:
        return parsed[0]
    position = q * Decimal(len(parsed) - 1)
    lower = int(position)
    upper = min(lower + 1, len(parsed) - 1)
    fraction = position - Decimal(lower)
    return parsed[lower] + (parsed[upper] - parsed[lower]) * fraction


def classify_three_level(
    value: Decimal | str | None,
    *,
    low_entry: Decimal | str,
    high_entry: Decimal | str,
) -> str | None:
    """Classify a scalar into LOW/NORMAL/HIGH using ordered boundaries."""
    if value is None:
        return None
    low = _decimal(low_entry)
    high = _decimal(high_entry)
    if low >= high:
        raise ValueError("low_entry must be smaller than high_entry")
    current = _decimal(value)
    if current < low:
        return "LOW"
    if current > high:
        return "HIGH"
    return "NORMAL"


def classify_trend(
    value: Decimal | str | None,
    *,
    down_entry: Decimal | str,
    up_entry: Decimal | str,
) -> str | None:
    """Classify a signed trend score into DOWN/NEUTRAL/UP."""
    if value is None:
        return None
    down = _decimal(down_entry)
    up = _decimal(up_entry)
    if down >= up:
        raise ValueError("down_entry must be smaller than up_entry")
    current = _decimal(value)
    if current < down:
        return "DOWN"
    if current > up:
        return "UP"
    return "NEUTRAL"


def _decimal(value: Decimal | str) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("value must be a valid decimal") from exc
