from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.features.models import FeatureSnapshot

T = datetime(2026, 1, 1, tzinfo=timezone.utc)


def snapshot(**overrides: object) -> FeatureSnapshot:
    values: dict[str, object] = {
        "decision_time": T,
        "trend_score": None,
        "realized_volatility": None,
        "breadth": None,
        "cross_sectional_dispersion": None,
        "average_pairwise_correlation": None,
        "asset_count": 1,
    }
    values.update(overrides)
    return FeatureSnapshot(**values)  # type: ignore[arg-type]


def test_snapshot_accepts_zero_asset_count() -> None:
    snapshot(asset_count=0)


def test_snapshot_rejects_negative_asset_count() -> None:
    with pytest.raises(ValueError, match="asset_count"):
        snapshot(asset_count=-1)


def test_snapshot_rejects_naive_time() -> None:
    with pytest.raises(ValueError, match="UTC"):
        snapshot(decision_time=datetime(2026, 1, 1))


@pytest.mark.parametrize("field", ["trend_score", "realized_volatility", "breadth", "cross_sectional_dispersion", "average_pairwise_correlation"])
def test_snapshot_rejects_non_finite_feature(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        snapshot(**{field: Decimal("NaN")})


@pytest.mark.parametrize("value", [Decimal("-0.01"), Decimal("-1")])
def test_realized_volatility_cannot_be_negative(value: Decimal) -> None:
    with pytest.raises(ValueError, match="realized_volatility"):
        snapshot(realized_volatility=value)


@pytest.mark.parametrize("value", [Decimal("-0.01"), Decimal("1.01")])
def test_breadth_must_be_between_zero_and_one(value: Decimal) -> None:
    with pytest.raises(ValueError, match="breadth"):
        snapshot(breadth=value)


@pytest.mark.parametrize("value", [Decimal("-1.01"), Decimal("1.01")])
def test_average_correlation_must_be_between_minus_one_and_one(value: Decimal) -> None:
    with pytest.raises(ValueError, match="average_pairwise_correlation"):
        snapshot(average_pairwise_correlation=value)


def test_cross_sectional_dispersion_cannot_be_negative() -> None:
    with pytest.raises(ValueError, match="cross_sectional_dispersion"):
        snapshot(cross_sectional_dispersion=Decimal("-0.01"))


def test_feature_boundaries_are_accepted() -> None:
    snapshot(
        realized_volatility=Decimal("0"),
        breadth=Decimal("0"),
        average_pairwise_correlation=Decimal("-1"),
        cross_sectional_dispersion=Decimal("0"),
    )
    snapshot(breadth=Decimal("1"), average_pairwise_correlation=Decimal("1"))
