from decimal import Decimal

import pytest

from trading_system.data.research.cross_sectional import (
    breadth,
    cross_sectional_dispersion,
    cross_sectional_rank,
)


def test_cross_sectional_rank_is_deterministic_and_normalized():
    result = cross_sectional_rank({"B": "0.20", "A": "0.10", "C": "0.30"})
    assert result == {"A": Decimal("0"), "B": Decimal("0.5"), "C": Decimal("1")}


def test_cross_sectional_rank_averages_ties():
    result = cross_sectional_rank({"A": "1", "B": "2", "C": "2", "D": "4"})
    assert result["A"] == Decimal("0")
    assert result["B"] == result["C"] == Decimal("0.5")
    assert result["D"] == Decimal("1")


def test_cross_sectional_rank_can_reverse_direction():
    result = cross_sectional_rank({"A": "1", "B": "2", "C": "3"}, higher_is_better=False)
    assert result == {"A": Decimal("1"), "B": Decimal("0.5"), "C": Decimal("0")}


def test_cross_sectional_rank_excludes_missing_values_without_imputation():
    result = cross_sectional_rank({"A": "1", "B": None, "C": "3"})
    assert result == {"A": Decimal("0"), "C": Decimal("1")}


def test_cross_sectional_rank_single_member_is_defined():
    assert cross_sectional_rank({"BTC": "0.10"}) == {"BTC": Decimal("1")}


def test_cross_sectional_rank_empty_input_is_empty():
    assert cross_sectional_rank({}) == {}
    assert cross_sectional_rank({"A": None}) == {}


def test_breadth_uses_valid_cross_section_as_denominator():
    result = breadth({"A": "0.10", "B": "-0.02", "C": None, "D": "0"})
    assert result == (Decimal("0.5"), 1, 3, True)


def test_breadth_supports_explicit_threshold():
    result = breadth(
        {"A": "0.02", "B": "0.05", "C": "0.10"},
        positive_threshold="0.05",
    )
    assert result == (Decimal(1) / Decimal(3), 1, 3, True)


def test_breadth_returns_insufficient_when_cross_section_is_too_small():
    assert breadth({"A": "0.10"}, minimum_count=2) == (None, 0, 1, False)


def test_breadth_rejects_non_positive_minimum_count():
    with pytest.raises(ValueError, match="minimum_count"):
        breadth({"A": "0.1"}, minimum_count=0)


def test_cross_sectional_dispersion_is_zero_for_identical_values():
    assert cross_sectional_dispersion({"A": "0.1", "B": "0.1", "C": "0.1"}) == Decimal("0")


def test_cross_sectional_dispersion_matches_population_standard_deviation():
    result = cross_sectional_dispersion({"A": "-1", "B": "0", "C": "1"})
    assert result == (Decimal(2) / Decimal(3)).sqrt()


def test_cross_sectional_dispersion_excludes_missing_values():
    assert cross_sectional_dispersion({"A": "-1", "B": None, "C": "1"}) == Decimal("1")


def test_cross_sectional_dispersion_returns_none_for_insufficient_data():
    assert cross_sectional_dispersion({"A": "0.1"}) is None
    assert cross_sectional_dispersion({"A": None, "B": "0.1"}, minimum_count=2) is None


def test_cross_sectional_dispersion_does_not_clip_extreme_observations():
    result = cross_sectional_dispersion({"A": "0", "B": "1", "C": "100"})
    mean = Decimal(101) / Decimal(3)
    variance = sum((value - mean) ** 2 for value in map(Decimal, ["0", "1", "100"])) / Decimal(3)
    assert result == variance.sqrt()


def test_cross_sectional_dispersion_rejects_invalid_minimum_count():
    with pytest.raises(ValueError, match="minimum_count"):
        cross_sectional_dispersion({"A": "0.1", "B": "0.2"}, minimum_count=1)
