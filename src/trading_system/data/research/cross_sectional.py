"""Point-in-time cross-sectional research feature primitives.

These functions operate on one already-selected cross-section at one decision
time. They do not discover universe membership, fetch data, or infer missing
observations.
"""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation


def cross_sectional_rank(
    values: Mapping[str, Decimal | str | None],
    *,
    higher_is_better: bool = True,
) -> dict[str, Decimal]:
    """Return deterministic percentile ranks for one cross-section.

    The lowest value receives 0 and the highest receives 1 when
    ``higher_is_better`` is true. Ties receive their average rank. Missing
    values are excluded rather than imputed. A one-member cross-section
    receives rank 1 because no relative ordering is possible.
    """
    if not values:
        return {}

    parsed = {
        instrument_id: _decimal(value)
        for instrument_id, value in values.items()
        if value is not None
    }
    if not parsed:
        return {}

    ordered = sorted(parsed.items(), key=lambda item: (item[1], item[0]))
    n = len(ordered)
    result: dict[str, Decimal] = {}
    index = 0

    while index < n:
        value = ordered[index][1]
        end = index + 1
        while end < n and ordered[end][1] == value:
            end += 1

        average_rank = (Decimal(index + 1) + Decimal(end)) / Decimal("2")
        percentile = (
            Decimal("1")
            if n == 1
            else (average_rank - Decimal("1")) / Decimal(n - 1)
        )
        if not higher_is_better:
            percentile = Decimal("1") - percentile

        for instrument_id, _ in ordered[index:end]:
            result[instrument_id] = percentile
        index = end

    return result


def breadth(
    values: Mapping[str, Decimal | str | None],
    *,
    positive_threshold: Decimal | str = Decimal("0"),
    minimum_count: int = 1,
) -> tuple[Decimal | None, int, int, bool]:
    """Measure the fraction of valid assets whose value exceeds a threshold.

    ``values`` should contain eligible/readiness-complete assets at one
    decision time. Missing observations are excluded from both numerator and
    denominator. Returns ``(ratio, positive_count, valid_count, sufficient)``.
    """
    if minimum_count <= 0:
        raise ValueError("minimum_count must be positive")

    threshold = _decimal(positive_threshold)
    valid = [_decimal(value) for value in values.values() if value is not None]
    valid_count = len(valid)
    if valid_count < minimum_count:
        return None, 0, valid_count, False

    positive_count = sum(value > threshold for value in valid)
    ratio = Decimal(positive_count) / Decimal(valid_count)
    return ratio, positive_count, valid_count, True


def cross_sectional_dispersion(
    values: Mapping[str, Decimal | str | None],
    *,
    minimum_count: int = 2,
) -> Decimal | None:
    """Return population standard deviation across one cross-section.

    Missing observations are excluded. Extreme observations are retained; this
    primitive performs no clipping or winsorization.
    """
    if minimum_count <= 1:
        raise ValueError("minimum_count must be greater than one")

    valid = [_decimal(value) for value in values.values() if value is not None]
    if len(valid) < minimum_count:
        return None

    mean = sum(valid, Decimal("0")) / Decimal(len(valid))
    variance = sum((value - mean) ** 2 for value in valid) / Decimal(len(valid))
    return variance.sqrt()


def _decimal(value: Decimal | str) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("value must be a valid decimal") from exc
