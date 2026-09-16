from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.features.models import FeatureSnapshot
from trading_system.research.dataset import ResearchDataset, ResearchObservation
from trading_system.research.split import chronological_split


def observation(hour: int) -> ResearchObservation:
    t = datetime(2026, 1, 1, hour, tzinfo=timezone.utc)
    features = FeatureSnapshot(t, Decimal("0"), Decimal("1"), Decimal("0.5"), Decimal("0.1"), Decimal("0"), 2)
    return ResearchObservation(t, features)


def test_chronological_split_has_no_overlap() -> None:
    dataset = ResearchDataset.from_observations(observation(h) for h in range(6))
    split = chronological_split(dataset, train_end=datetime(2026, 1, 1, 3, tzinfo=timezone.utc))
    assert [x.decision_time.hour for x in split.train.observations] == [0, 1, 2]
    assert [x.decision_time.hour for x in split.test.observations] == [3, 4, 5]


def test_bounded_test_window() -> None:
    dataset = ResearchDataset.from_observations(observation(h) for h in range(6))
    split = chronological_split(
        dataset,
        train_end=datetime(2026, 1, 1, 2, tzinfo=timezone.utc),
        test_end=datetime(2026, 1, 1, 5, tzinfo=timezone.utc),
    )
    assert len(split.train.observations) == 2
    assert len(split.test.observations) == 3


def test_rejects_empty_splits() -> None:
    dataset = ResearchDataset.from_observations(observation(h) for h in range(3))
    with pytest.raises(ValueError):
        chronological_split(dataset, train_end=datetime(2025, 1, 1, tzinfo=timezone.utc))
    with pytest.raises(ValueError):
        chronological_split(dataset, train_end=datetime(2026, 1, 1, 10, tzinfo=timezone.utc))


def test_rejects_reversed_bounds() -> None:
    dataset = ResearchDataset.from_observations(observation(h) for h in range(3))
    with pytest.raises(ValueError):
        chronological_split(
            dataset,
            train_end=datetime(2026, 1, 1, 2, tzinfo=timezone.utc),
            test_end=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        )
