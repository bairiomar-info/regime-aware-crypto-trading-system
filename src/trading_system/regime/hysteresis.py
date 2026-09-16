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
    previous_candidate_state: str | None = None,
    state_age: int = 0,
    config: HysteresisConfig | None = None,
) -> HysteresisResult:
    """Advance one observation using temporal confirmation only.

    A new candidate is accepted after the configured number of consecutive
    observations. If the pending candidate changes, confirmation restarts;
    observations of different candidate states are never combined.

    ``previous_candidate_state`` is optional for compatibility with the
    primitive API: when omitted, a non-zero confirmation count is treated as
    belonging to the supplied candidate. Stateful callers should always pass
    the previous candidate explicitly so candidate changes reset confirmation.
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

    same_pending_candidate = (
        previous_candidate_state is None or previous_candidate_state == candidate_state
    )
    count = confirmation_count + 1 if same_pending_candidate else 1
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
