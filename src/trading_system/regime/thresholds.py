"""Past-only empirical threshold helpers for regime classification."""

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation


def empirical_quantile(values: Sequence[Decimal | str], quantile: Decimal | str) -> Decimal | None:
    """Return a deterministic linearly interpolated empirical quantile.

    The caller must provide a point-in-time historical window. This helper does
    not fetch data or impose a research-optimal window/quantile.
    """
    q = _finite_decimal(quantile)
    if not 0 <= q <= 1:
        raise ValueError("quantile must be between zero and one")
    parsed = sorted(_finite_decimal(v) for v in values)
    if not parsed:
        return None
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
    """Classify a scalar into LOW/NORMAL/HIGH using ordered entry boundaries."""
    if value is None:
        return None
    low = _finite_decimal(low_entry)
    high = _finite_decimal(high_entry)
    if low >= high:
        raise ValueError("low_entry must be smaller than high_entry")
    current = _finite_decimal(value)
    if current < low:
        return "LOW"
    if current > high:
        return "HIGH"
    return "NORMAL"


def classify_three_level_hysteresis(
    value: Decimal | str | None,
    *,
    accepted_state: str | None,
    low_entry: Decimal | str,
    low_exit: Decimal | str,
    high_exit: Decimal | str,
    high_entry: Decimal | str,
) -> str | None:
    """Classify LOW/NORMAL/HIGH with separate entry and exit boundaries."""
    if value is None:
        return None
    low_entry_d = _finite_decimal(low_entry)
    low_exit_d = _finite_decimal(low_exit)
    high_exit_d = _finite_decimal(high_exit)
    high_entry_d = _finite_decimal(high_entry)
    if not low_entry_d < low_exit_d < high_exit_d < high_entry_d:
        raise ValueError(
            "boundaries must satisfy low_entry < low_exit < high_exit < high_entry"
        )

    current = _finite_decimal(value)
    if accepted_state == "LOW" and current < low_exit_d:
        return "LOW"
    if accepted_state == "HIGH" and current > high_exit_d:
        return "HIGH"
    return classify_three_level(current, low_entry=low_entry_d, high_entry=high_entry_d)


def classify_trend(
    value: Decimal | str | None,
    *,
    down_entry: Decimal | str,
    up_entry: Decimal | str,
) -> str | None:
    """Classify a signed trend score into DOWN/NEUTRAL/UP using entry boundaries."""
    if value is None:
        return None
    down = _finite_decimal(down_entry)
    up = _finite_decimal(up_entry)
    if down >= up:
        raise ValueError("down_entry must be smaller than up_entry")
    current = _finite_decimal(value)
    if current < down:
        return "DOWN"
    if current > up:
        return "UP"
    return "NEUTRAL"


def classify_trend_hysteresis(
    value: Decimal | str | None,
    *,
    accepted_state: str | None,
    down_entry: Decimal | str,
    down_exit: Decimal | str,
    up_exit: Decimal | str,
    up_entry: Decimal | str,
) -> str | None:
    """Classify DOWN/NEUTRAL/UP with separate entry and exit boundaries."""
    if value is None:
        return None
    down_entry_d = _finite_decimal(down_entry)
    down_exit_d = _finite_decimal(down_exit)
    up_exit_d = _finite_decimal(up_exit)
    up_entry_d = _finite_decimal(up_entry)
    if not down_entry_d < down_exit_d < up_exit_d < up_entry_d:
        raise ValueError(
            "boundaries must satisfy down_entry < down_exit < up_exit < up_entry"
        )

    current = _finite_decimal(value)
    if accepted_state == "DOWN" and current < down_exit_d:
        return "DOWN"
    if accepted_state == "UP" and current > up_exit_d:
        return "UP"
    return classify_trend(current, down_entry=down_entry_d, up_entry=up_entry_d)


def _finite_decimal(value: Decimal | str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("value must be a valid decimal") from exc
    if not parsed.is_finite():
        raise ValueError("value must be finite")
    return parsed
