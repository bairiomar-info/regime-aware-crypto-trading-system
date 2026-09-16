from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.features.models import FeatureSnapshot
from trading_system.research.dataset import ResearchDataset, ResearchObservation
from trading_system.research.split import chronological_split
from trading_system.research.walk_forward import WalkForwardConfig, walk_forward_plan


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def observation(hour: int, *, forward_return: Decimal | None = None) -> ResearchObservation:
    decision_time = START + timedelta(hours=hour)
    features = FeatureSnapshot(
        decision_time,
        Decimal("0"),
        Decimal("1"),
        Decimal("0.5"),
        Decimal("0.1"),
        Decimal("0"),
        2,
    )
    return ResearchObservation(decision_time, features, forward_return)


def dataset(hours: list[int]) -> ResearchDataset:
    return ResearchDataset.from_observations(observation(hour) for hour in hours)


def test_count_windows_are_fixed_chronological_and_leakage_safe() -> None:
    plan = walk_forward_plan(
        dataset(list(range(10))),
        WalkForwardConfig(train_size=3, test_size=2, step_size=2, min_train_observations=3),
    )

    assert len(plan.windows) == 3
    assert [[item.decision_time.hour for item in window.train.observations] for window in plan.windows] == [
        [0, 1, 2],
        [2, 3, 4],
        [4, 5, 6],
    ]
    assert [[item.decision_time.hour for item in window.test.observations] for window in plan.windows] == [
        [3, 4],
        [5, 6],
        [7, 8],
    ]
    for window in plan.windows:
        assert max(item.decision_time for item in window.train.observations) < min(
            item.decision_time for item in window.test.observations
        )
        assert all(window.test_start <= item.decision_time < window.test_end for item in window.test.observations)


def test_final_partial_test_window_is_not_emitted() -> None:
    plan = walk_forward_plan(dataset(list(range(6))), WalkForwardConfig(train_size=2, test_size=3, step_size=3))
    assert len(plan.windows) == 1
    assert [item.decision_time.hour for item in plan.windows[0].test.observations] == [2, 3, 4]


def test_step_larger_than_dataset_still_emits_first_complete_window() -> None:
    plan = walk_forward_plan(dataset(list(range(8))), WalkForwardConfig(train_size=2, test_size=2, step_size=99))
    assert len(plan.windows) == 1


def test_overlapping_test_windows_require_explicit_opt_in() -> None:
    with pytest.raises(ValueError, match="allow_test_overlap"):
        WalkForwardConfig(train_size=3, test_size=3, step_size=1)

    plan = walk_forward_plan(
        dataset(list(range(8))),
        WalkForwardConfig(train_size=3, test_size=3, step_size=1, allow_test_overlap=True),
    )
    assert [[item.decision_time.hour for item in window.test.observations] for window in plan.windows] == [
        [3, 4, 5],
        [4, 5, 6],
        [5, 6, 7],
    ]


def test_timedelta_windows_use_half_open_boundaries_with_irregular_timestamps() -> None:
    plan = walk_forward_plan(
        dataset([0, 2, 3, 5, 7, 10]),
        WalkForwardConfig(
            train_size=timedelta(hours=3),
            test_size=timedelta(hours=2),
            step_size=timedelta(hours=2),
        ),
    )
    assert [window.test_start.hour for window in plan.windows] == [2, 5, 7]
    assert [[item.decision_time.hour for item in window.test.observations] for window in plan.windows] == [[2, 3], [5], [7]]
    assert plan.windows[1].train_start == START + timedelta(hours=2)


def test_timedelta_test_end_excludes_observation_on_exact_boundary() -> None:
    plan = walk_forward_plan(
        dataset([0, 1, 2, 3, 4, 5]),
        WalkForwardConfig(
            train_size=timedelta(hours=2),
            test_size=timedelta(hours=2),
            step_size=timedelta(hours=2),
            min_train_observations=2,
        ),
    )
    assert [item.decision_time.hour for item in plan.windows[0].test.observations] == [2, 3]
    assert plan.windows[0].test_end == START + timedelta(hours=4)


@pytest.mark.parametrize(
    ("config", "message"),
    [
        (WalkForwardConfig(train_size=2, test_size=1, step_size=1), "no complete"),
        (WalkForwardConfig(train_size=timedelta(hours=100), test_size=timedelta(hours=1), step_size=timedelta(hours=1)), "no complete"),
    ],
)
def test_insufficient_history_and_single_observation_are_explicit(config: WalkForwardConfig, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        walk_forward_plan(dataset([0]), config)


def test_empty_dataset_is_rejected() -> None:
    with pytest.raises(ValueError, match="dataset must not be empty"):
        walk_forward_plan(ResearchDataset(()), WalkForwardConfig(train_size=1, test_size=1, step_size=1))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"train_size": 0, "test_size": 1, "step_size": 1},
        {"train_size": 1, "test_size": timedelta(0), "step_size": 1},
        {"train_size": 1, "test_size": 1, "step_size": -1},
        {"train_size": 2, "test_size": 1, "step_size": 1, "min_train_observations": 3},
    ],
)
def test_impossible_configurations_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        WalkForwardConfig(**kwargs)


def test_future_observation_mutation_cannot_change_an_earlier_fold() -> None:
    original = dataset(list(range(9)))
    changed_rows = list(original.observations)
    changed_rows[-1] = observation(8, forward_return=Decimal("999"))
    changed = ResearchDataset.from_observations(changed_rows)
    config = WalkForwardConfig(train_size=3, test_size=2, step_size=2)

    assert walk_forward_plan(original, config).windows[0] == walk_forward_plan(changed, config).windows[0]


def test_dataset_and_split_reject_mutability_and_non_utc_boundaries() -> None:
    row = observation(0)
    with pytest.raises(TypeError, match="tuple"):
        ResearchDataset([row])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="UTC"):
        chronological_split(dataset([0, 1]), train_end=datetime(2026, 1, 1, 1))
    with pytest.raises(TypeError, match="Decimal"):
        ResearchObservation(row.decision_time, row.features, forward_return="0")  # type: ignore[arg-type]
