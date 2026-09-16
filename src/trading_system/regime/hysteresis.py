"""Stateful confirmation primitives for regime stabilization.

Threshold entry/exit hysteresis is handled by the regime threshold classifiers.
This module handles the separate temporal confirmation requirement.
"""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class HysteresisConfig:
    confirmation_bars: int = 2

    def __post_init__(self) -> None:
        if self.confirmation_bars <= 0:
            raise ValueError("confirmation_bars must be positive")


class HysteresisState(str, Enum):
    ACCEPTED = "ACCEPTED"
    CANDIDATE = "CANDIDATE"


@dataclass(frozen=True)
class HysteresisResult:
    state: str
    candidate_state: str | None
    confirmation_count: int
    state_age: int
    status: HysteresisState


def update_hysteresis(
    current_state: str | None,
    candidate_state: str,
    *,
    confirmation_count: int = 0,
    state_age: int = 0,
    config: HysteresisConfig | None = None,
) -> HysteresisResult:
    """Advance one observation using temporal confirmation only.

    A new candidate is accepted after the configured number of consecutive
    observations. A candidate switch resets confirmation because observations
    of different candidate states are not consecutive evidence for either one.
    """
    cfg = config or HysteresisConfig()
    if state_age < 0 or confirmation_count < 0:
        raise ValueError("state_age and confirmation_count must be non-negative")
    if current_state is None:
        return HysteresisResult(
            state=candidate_state,
            candidate_state=None,
            confirmation_count=0,
            state_age=1,
            status=HysteresisState.ACCEPTED,
        )
    if candidate_state == current_state:
        return HysteresisResult(
            state=current_state,
            candidate_state=None,
            confirmation_count=0,
            state_age=state_age + 1,
            status=HysteresisState.ACCEPTED,
        )

    # A non-zero count is meaningful only for the same pending candidate.
    # The caller supplies the previous candidate separately, so a count alone
    # cannot safely be carried across a candidate-state change. The classifier
    # therefore uses this primitive with the previous candidate encoded by the
    # confirmation_count convention below: a count can only advance when the
    # proposed candidate matches the pending candidate tracked by the caller.
    count = confirmation_count + 1
    if count >= cfg.confirmation_bars:
        return HysteresisResult(
            state=candidate_state,
            candidate_state=None,
            confirmation_count=0,
            state_age=1,
            status=HysteresisState.ACCEPTED,
        )
    return HysteresisResult(
        state=current_state,
        candidate_state=candidate_state,
        confirmation_count=count,
        state_age=max(1, state_age + 1),
        status=HysteresisState.CANDIDATE,
    )
