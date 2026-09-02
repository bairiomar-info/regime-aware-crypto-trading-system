from decimal import Decimal
from enum import Enum

import pytest

from trading_system.data.research.redundancy import (
    pairwise_spearman_matrix,
    spearman_rank_correlation,
    state_agreement,
)


class State(Enum):
    UP = "up"
    DOWN = "down"


def test_spearman_perfect_positive_order():
    correlation, count = spearman_rank_correlation([1, 2, 3], [10, 20, 30])
    assert correlation == Decimal("1")
    assert count == 3


def test_spearman_perfect_negative_order():
    correlation, count = spearman_rank_correlation([1, 2, 3], [30, 20, 10])
    assert correlation == Decimal("-1")
    assert count == 3


def test_spearman_uses_average_ranks_for_ties():
    correlation, count = spearman_rank_correlation([1, 1, 2, 3], [10, 20, 20, 40])
    assert correlation == pytest.approx(Decimal("0.8333333333333333333333333333"))
    assert count == 4


def test_spearman_excludes_missing_pairs():
    correlation, count = spearman_rank_correlation(
        [1, None, 3, 4], [10, 20, None, 40]
    )
    assert correlation == Decimal("1")
    assert count == 2


def test_spearman_returns_none_when_below_minimum_count():
    correlation, count = spearman_rank_correlation([1, None], [2, 3], minimum_count=2)
    assert correlation is None
    assert count == 1


def test_spearman_returns_none_for_constant_series():
    correlation, count = spearman_rank_correlation([1, 1, 1], [1, 2, 3])
    assert correlation is None
    assert count == 3


def test_spearman_requires_equal_lengths():
    with pytest.raises(ValueError, match="equal lengths"):
        spearman_rank_correlation([1, 2], [1])


def test_pairwise_matrix_is_deterministic_and_excludes_diagonal():
    result = pairwise_spearman_matrix(
        {
            "volatility": [1, 2, 3],
            "trend": [3, 2, 1],
            "breadth": [1, 3, 2],
        }
    )
    assert list(result) == [
        ("breadth", "trend"),
        ("breadth", "volatility"),
        ("trend", "volatility"),
    ]
    assert result[("trend", "volatility")][0] == Decimal("-1")


def test_state_agreement_compares_exact_values_and_excludes_missing():
    comparable, agreements, ratio = state_agreement(
        [State.UP, None, State.DOWN, "up"],
        ["up", State.DOWN, State.DOWN, State.DOWN],
    )
    assert comparable == 3
    assert agreements == 2
    assert ratio == Decimal("2") / Decimal("3")


def test_state_agreement_returns_none_ratio_without_comparisons():
    assert state_agreement([None], [State.UP]) == (0, 0, None)


def test_state_agreement_requires_equal_lengths():
    with pytest.raises(ValueError, match="equal lengths"):
        state_agreement([State.UP], [State.UP, State.DOWN])
