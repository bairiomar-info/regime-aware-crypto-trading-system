"""Point-in-time correlation research primitives.

These functions operate on already-selected, aligned historical return
windows. They do not fetch data, infer missing observations, or choose a
universe. Correlation is treated as a descriptive dependence/risk feature,
not as a trading signal by itself.
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation


def pairwise_correlation(
    left: Sequence[Decimal | str | None],
    right: Sequence[Decimal | str | None],
    *,
    minimum_count: int = 2,
) -> Decimal | None:
    """Return Pearson correlation using only complete paired observations.

    The two sequences must be aligned to the same decision-time window. Missing
    observations are excluded pairwise rather than imputed. A constant series
    has undefined correlation and returns ``None``.
    """
    if minimum_count <= 1:
        raise ValueError("minimum_count must be greater than one")
    if len(left) != len(right):
        raise ValueError("left and right must have equal lengths")

    pairs = [
        (_decimal(x), _decimal(y))
        for x, y in zip(left, right)
        if x is not None and y is not None
    ]
    if len(pairs) < minimum_count:
        return None

    mean_left = sum((x for x, _ in pairs), Decimal("0")) / Decimal(len(pairs))
    mean_right = sum((y for _, y in pairs), Decimal("0")) / Decimal(len(pairs))
    covariance = sum(
        (x - mean_left) * (y - mean_right) for x, y in pairs
    )
    variance_left = sum((x - mean_left) ** 2 for x, _ in pairs)
    variance_right = sum((y - mean_right) ** 2 for _, y in pairs)
    denominator = (variance_left * variance_right).sqrt()
    if denominator == 0:
        return None
    return covariance / denominator


def average_pairwise_correlation(
    returns: Mapping[str, Sequence[Decimal | str | None]],
    *,
    minimum_count: int = 2,
) -> tuple[Decimal | None, int, bool]:
    """Return the mean valid pairwise correlation for one cross-section.

    Asset identifiers are sorted deterministically before pairs are evaluated.
    Invalid/undefined pairs are excluded. The result is
    ``(average, valid_pair_count, sufficient)``. The feature is intended for
    market-state and portfolio-risk analysis, not direct entry/exit decisions.
    """
    if minimum_count <= 1:
        raise ValueError("minimum_count must be greater than one")

    identifiers = sorted(returns)
    correlations: list[Decimal] = []
    for index, left_id in enumerate(identifiers):
        for right_id in identifiers[index + 1 :]:
            value = pairwise_correlation(
                returns[left_id], returns[right_id], minimum_count=minimum_count
            )
            if value is not None:
                correlations.append(value)

    if not correlations:
        return None, 0, False
    average = sum(correlations, Decimal("0")) / Decimal(len(correlations))
    return average, len(correlations), True


def _decimal(value: Decimal | str) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("value must be a valid decimal") from exc
