"""Reusable, leakage-safe rolling windows for chronological research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .dataset import ResearchDataset, ResearchObservation
from .time import require_utc


WindowSize = int | timedelta


@dataclass(frozen=True)
class WalkForwardConfig:
    """Fixed rolling-window settings expressed in observations or elapsed time.

    Integer sizes count observations. ``timedelta`` sizes describe half-open
    timestamp intervals. These forms can be combined deliberately, for example
    to train on a fixed observation count and test for a calendar period. Test
    overlap is forbidden by default because treating overlapping out-of-sample
    samples as independent is an easy research error.
    """

    train_size: WindowSize
    test_size: WindowSize
    step_size: WindowSize
    min_train_observations: int = 1
    allow_test_overlap: bool = False

    def __post_init__(self) -> None:
        for name in ("train_size", "test_size", "step_size"):
            _validate_size(getattr(self, name), name=name)
        if not isinstance(self.min_train_observations, int) or isinstance(self.min_train_observations, bool):
            raise TypeError("min_train_observations must be an int")
        if self.min_train_observations < 1:
            raise ValueError("min_train_observations must be at least 1")
        if not isinstance(self.allow_test_overlap, bool):
            raise TypeError("allow_test_overlap must be a bool")
        if isinstance(self.train_size, int) and self.min_train_observations > self.train_size:
            raise ValueError("min_train_observations cannot exceed integer train_size")
        if (
            not self.allow_test_overlap
            and type(self.test_size) is type(self.step_size)
            and self.step_size < self.test_size
        ):
            raise ValueError("step_size smaller than test_size requires allow_test_overlap=True")


@dataclass(frozen=True)
class WalkForwardWindow:
    """One immutable train/test fold with explicit exclusive time boundaries."""

    ordinal: int
    train: ResearchDataset
    test: ResearchDataset
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.ordinal, int) or isinstance(self.ordinal, bool):
            raise TypeError("ordinal must be an int")
        if self.ordinal < 0:
            raise ValueError("ordinal must be non-negative")
        if not isinstance(self.train, ResearchDataset) or not isinstance(self.test, ResearchDataset):
            raise TypeError("train and test must be ResearchDataset values")
        if not self.train.observations:
            raise ValueError("train window must not be empty")
        if not self.test.observations:
            raise ValueError("test window must not be empty")
        for name in ("train_start", "train_end", "test_start", "test_end"):
            require_utc(getattr(self, name), name=name)
        if not self.train_start < self.train_end == self.test_start < self.test_end:
            raise ValueError("window boundaries must be ordered with train_end equal to test_start")
        if self.train.observations[0].decision_time < self.train_start:
            raise ValueError("train observation precedes train_start")
        if self.train.observations[-1].decision_time >= self.train_end:
            raise ValueError("training data must precede test_start")
        if self.test.observations[0].decision_time < self.test_start:
            raise ValueError("test observation precedes test_start")
        if self.test.observations[-1].decision_time >= self.test_end:
            raise ValueError("test observation must precede test_end")


@dataclass(frozen=True)
class WalkForwardPlan:
    """Deterministic collection of chronological walk-forward windows."""

    config: WalkForwardConfig
    windows: tuple[WalkForwardWindow, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.config, WalkForwardConfig):
            raise TypeError("config must be a WalkForwardConfig")
        if not isinstance(self.windows, tuple):
            raise TypeError("windows must be a tuple")
        if not self.windows:
            raise ValueError("walk-forward plan must contain at least one window")
        seen_test_times: set[datetime] = set()
        previous_start: datetime | None = None
        for ordinal, window in enumerate(self.windows):
            if not isinstance(window, WalkForwardWindow):
                raise TypeError("windows must contain WalkForwardWindow values")
            if window.ordinal != ordinal:
                raise ValueError("window ordinals must be consecutive")
            if previous_start is not None and window.test_start <= previous_start:
                raise ValueError("test starts must be strictly increasing")
            if not self.config.allow_test_overlap:
                overlap = seen_test_times.intersection(item.decision_time for item in window.test.observations)
                if overlap:
                    raise ValueError("test observations must not overlap")
            seen_test_times.update(item.decision_time for item in window.test.observations)
            previous_start = window.test_start


def walk_forward_plan(dataset: ResearchDataset, config: WalkForwardConfig) -> WalkForwardPlan:
    """Build complete causal windows without fitting or evaluating a strategy.

    A fold is emitted only when both its training and test data are complete.
    For an integer test size, completeness means exactly that many observations.
    For an elapsed-time test size, the requested exclusive test end must not
    extend beyond the dataset's final timestamp. This conservative rule avoids
    presenting a truncated terminal interval as an out-of-sample period.
    """
    if not dataset.observations:
        raise ValueError("dataset must not be empty")

    observations = dataset.observations
    windows: list[WalkForwardWindow] = []
    last_selected_index: int | None = None
    last_selected_time: datetime | None = None

    for index, anchor in enumerate(observations):
        if not _step_reached(
            index=index,
            anchor=anchor.decision_time,
            previous_index=last_selected_index,
            previous_time=last_selected_time,
            step_size=config.step_size,
        ):
            continue

        train, train_start = _training_data(observations, index=index, anchor=anchor.decision_time, size=config.train_size)
        if len(train) < config.min_train_observations:
            continue

        test, test_end, complete = _test_data(observations, index=index, anchor=anchor.decision_time, size=config.test_size)
        if not complete:
            break
        if not test:
            raise ValueError("test window must not be empty")

        windows.append(
            WalkForwardWindow(
                ordinal=len(windows),
                train=ResearchDataset(train),
                test=ResearchDataset(test),
                train_start=train_start,
                train_end=anchor.decision_time,
                test_start=anchor.decision_time,
                test_end=test_end,
            )
        )
        last_selected_index = index
        last_selected_time = anchor.decision_time

    if not windows:
        raise ValueError("no complete walk-forward windows fit dataset and configuration")
    return WalkForwardPlan(config=config, windows=tuple(windows))


def _validate_size(value: WindowSize, *, name: str) -> None:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a positive int or timedelta")
    if isinstance(value, int):
        if value < 1:
            raise ValueError(f"{name} must be positive")
        return
    if isinstance(value, timedelta):
        if value <= timedelta(0):
            raise ValueError(f"{name} must be positive")
        return
    raise TypeError(f"{name} must be a positive int or timedelta")


def _step_reached(
    *,
    index: int,
    anchor: datetime,
    previous_index: int | None,
    previous_time: datetime | None,
    step_size: WindowSize,
) -> bool:
    if previous_index is None:
        return True
    if isinstance(step_size, int):
        return index >= previous_index + step_size
    assert previous_time is not None
    return anchor >= previous_time + step_size


def _training_data(
    observations: tuple[ResearchObservation, ...],
    *,
    index: int,
    anchor: datetime,
    size: WindowSize,
) -> tuple[tuple[ResearchObservation, ...], datetime]:
    if isinstance(size, int):
        if index < size:
            return (), anchor
        train = observations[index - size : index]
        return train, train[0].decision_time
    start = anchor - size
    return tuple(item for item in observations[:index] if item.decision_time >= start), start


def _test_data(
    observations: tuple[ResearchObservation, ...],
    *,
    index: int,
    anchor: datetime,
    size: WindowSize,
) -> tuple[tuple[ResearchObservation, ...], datetime, bool]:
    if isinstance(size, int):
        test = observations[index : index + size]
        if len(test) != size:
            return (), anchor, False
        # Integer windows have no inherent calendar end. Datetimes have
        # microsecond precision, so this is the smallest explicit exclusive
        # boundary containing the selected final observation.
        return test, test[-1].decision_time + timedelta(microseconds=1), True
    end = anchor + size
    if end > observations[-1].decision_time:
        return (), end, False
    test = tuple(item for item in observations[index:] if item.decision_time < end)
    return test, end, True
