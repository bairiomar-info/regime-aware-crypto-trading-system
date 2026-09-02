from decimal import Decimal

import pytest

from trading_system.data.research.correlation import (
    average_pairwise_correlation,
    pairwise_correlation,
)


def test_perfect_positive_correlation():
    result = pairwise_correlation(["1", "2", "3"], ["2", "4", "6"])
    assert result == Decimal("1")


def test_perfect_negative_correlation():
    result = pairwise_correlation(["1", "2", "3"], ["3", "2", "1"])
    assert result == Decimal("-1")


def test_missing_values_are_excluded_pairwise():
    result = pairwise_correlation(["1", None, "3", "4"], ["2", "4", None, "8"])
    assert result == Decimal("1")


def test_insufficient_complete_pairs():
    result = pairwise_correlation(["1", None], ["2", "3"], minimum_count=2)
    assert result is None


def test_length_mismatch_rejected():
    with pytest.raises(ValueError, match="equal lengths"):
        pairwise_correlation(["1", "2"], ["1"])


def test_constant_series_has_undefined_correlation():
    assert pairwise_correlation(["1", "1", "1"], ["1", "2", "3"]) is None


def test_invalid_decimal_rejected():
    with pytest.raises(ValueError, match="valid decimal"):
        pairwise_correlation(["1", "bad"], ["1", "2"])


def test_average_pairwise_correlation():
    result = average_pairwise_correlation(
        {
            "A": ["1", "2", "3"],
            "B": ["2", "4", "6"],
            "C": ["3", "2", "1"],
        }
    )
    assert result == (Decimal("-1") / Decimal("3"), 3, True)


def test_average_is_deterministic_over_mapping_order():
    first = average_pairwise_correlation(
        {"B": ["2", "4", "6"], "A": ["1", "2", "3"]}
    )
    second = average_pairwise_correlation(
        {"A": ["1", "2", "6"], "B": ["2", "4", "6"]}
    )
    assert first != second


def test_average_excludes_undefined_pairs():
    result = average_pairwise_correlation(
        {
            "A": ["1", "1", "1"],
            "B": ["1", "2", "3"],
            "C": ["1", "2", "3"],
        }
    )
    assert result == (Decimal("1"), 1, True)


def test_average_without_valid_pairs_is_insufficient():
    result = average_pairwise_correlation(
        {"A": ["1", "1"], "B": ["2", "2"]}
    )
    assert result == (None, 0, False)


def test_minimum_count_validation():
    with pytest.raises(ValueError, match="greater than one"):
        pairwise_correlation(["1", "2"], ["1", "2"], minimum_count=1)
    with pytest.raises(ValueError, match="greater than one"):
        average_pairwise_correlation({"A": ["1"], "B": ["2"]}, minimum_count=1)
