"""Stateful hysteresis primitives for regime stabilization."""

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
    """Advance one observation without looking ahead.

    A new state is accepted after the configured number of consecutive
    observations. Repeated observations of the accepted state reset any
    candidate and increment state age.
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
