"""Descriptive redundancy analysis primitives for regime dimensions.

These functions measure overlap between already-aligned research series. They
never use future observations, infer missing values, or make trading decisions.
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation


def spearman_rank_correlation(
    left: Sequence[Decimal | str | int | None],
    right: Sequence[Decimal | str | int | None],
    *,
    minimum_count: int = 2,
) -> tuple[Decimal | None, int]:
    """Return Spearman rank correlation and the number of valid pairs.

    Missing values are excluded pairwise. Ties receive average ranks. A
    constant ranked series has undefined correlation and returns ``None``.
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
    count = len(pairs)
    if count < minimum_count:
        return None, count

    left_ranks = _average_ranks([x for x, _ in pairs])
    right_ranks = _average_ranks([y for _, y in pairs])
    mean_left = sum(left_ranks, Decimal("0")) / Decimal(count)
    mean_right = sum(right_ranks, Decimal("0")) / Decimal(count)
    covariance = sum(
        (x - mean_left) * (y - mean_right)
        for x, y in zip(left_ranks, right_ranks)
    )
    variance_left = sum((x - mean_left) ** 2 for x in left_ranks)
    variance_right = sum((y - mean_right) ** 2 for y in right_ranks)
    denominator = (variance_left * variance_right).sqrt()
    if denominator == 0:
        return None, count
    return covariance / denominator, count


def pairwise_spearman_matrix(
    series: Mapping[str, Sequence[Decimal | str | int | None]],
    *,
    minimum_count: int = 2,
) -> dict[tuple[str, str], tuple[Decimal | None, int]]:
    """Return deterministic pairwise Spearman results for named series."""
    if minimum_count <= 1:
        raise ValueError("minimum_count must be greater than one")

    names = sorted(series)
    result: dict[tuple[str, str], tuple[Decimal | None, int]] = {}
    for index, left_name in enumerate(names):
        for right_name in names[index + 1 :]:
            result[(left_name, right_name)] = spearman_rank_correlation(
                series[left_name],
                series[right_name],
                minimum_count=minimum_count,
            )
    return result


def state_agreement(
    left: Sequence[object | None],
    right: Sequence[object | None],
) -> tuple[int, int, Decimal | None]:
    """Return comparable rows, exact agreements, and agreement ratio."""
    if len(left) != len(right):
        raise ValueError("left and right must have equal lengths")

    comparable = 0
    agreements = 0
    for left_state, right_state in zip(left, right):
        if left_state is None or right_state is None:
            continue
        comparable += 1
        if _state_value(left_state) == _state_value(right_state):
            agreements += 1

    if comparable == 0:
        return 0, 0, None
    return comparable, agreements, Decimal(agreements) / Decimal(comparable)


def _average_ranks(values: Sequence[Decimal]) -> list[Decimal]:
    indexed = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [Decimal("0")] * len(values)
    position = 0
    while position < len(indexed):
        end = position + 1
        value = indexed[position][1]
        while end < len(indexed) and indexed[end][1] == value:
            end += 1
        average_rank = (Decimal(position + 1) + Decimal(end)) / Decimal("2")
        for rank_index in range(position, end):
            original_index = indexed[rank_index][0]
            ranks[original_index] = average_rank
        position = end
    return ranks


def _state_value(value: object) -> object:
    return getattr(value, "value", value)


def _decimal(value: Decimal | str | int) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("value must be a valid decimal") from exc
