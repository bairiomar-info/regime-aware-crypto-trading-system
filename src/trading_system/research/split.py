"""Leakage-safe chronological research splits."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .dataset import ResearchDataset


@dataclass(frozen=True)
class ResearchSplit:
    """One chronological train/test partition."""

    train: ResearchDataset
    test: ResearchDataset


def chronological_split(
    dataset: ResearchDataset,
    *,
    train_end: datetime,
    test_end: datetime | None = None,
) -> ResearchSplit:
    """Split strictly by decision time; no observation crosses the boundary."""
    if dataset.observations == ():
        raise ValueError("dataset must not be empty")
    if test_end is not None and test_end <= train_end:
        raise ValueError("test_end must be after train_end")

    train_items = tuple(item for item in dataset.observations if item.decision_time < train_end)
    test_items = tuple(
        item
        for item in dataset.observations
        if item.decision_time >= train_end and (test_end is None or item.decision_time < test_end)
    )
    if not train_items:
        raise ValueError("train split must not be empty")
    if not test_items:
        raise ValueError("test split must not be empty")
    return ResearchSplit(ResearchDataset(train_items), ResearchDataset(test_items))
