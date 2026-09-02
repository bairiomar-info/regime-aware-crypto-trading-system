"""Point-in-time feature and strategy readiness contracts."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReadinessState(StrEnum):
    """Research readiness state for an instrument at a decision time."""

    NOT_READY = "not_ready"
    INSUFFICIENT_HISTORY = "insufficient_history"
    READY_FOR_FEATURES = "ready_for_features"
    READY_FOR_STRATEGY = "ready_for_strategy"


class ReadinessDecision(BaseModel):
    """Immutable readiness result with explicit required-history evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    instrument_id: str = Field(min_length=1)
    decision_time: object
    state: ReadinessState
    available_bars: int = Field(ge=0)
    required_bars: int = Field(ge=0)
    reason: str = Field(min_length=1)

    def model_post_init(self, __context: object) -> None:
        if self.state == ReadinessState.INSUFFICIENT_HISTORY and self.available_bars >= self.required_bars:
            raise ValueError("insufficient_history requires available_bars below required_bars")
        if self.state != ReadinessState.INSUFFICIENT_HISTORY and self.available_bars < self.required_bars:
            raise ValueError("readiness state cannot exceed available history")


def assess_readiness(
    *,
    instrument_id: str,
    decision_time,
    available_bars: int,
    required_bars: int,
    strategy_ready: bool = False,
) -> ReadinessDecision:
    """Assess readiness without imposing a universal asset-age threshold."""
    if available_bars < 0 or required_bars < 0:
        raise ValueError("bar counts must be non-negative")
    if available_bars < required_bars:
        state = ReadinessState.INSUFFICIENT_HISTORY
        reason = "insufficient_history"
    elif strategy_ready:
        state = ReadinessState.READY_FOR_STRATEGY
        reason = "strategy_requirements_satisfied"
    else:
        state = ReadinessState.READY_FOR_FEATURES
        reason = "feature_history_satisfied"
    return ReadinessDecision(
        instrument_id=instrument_id,
        decision_time=decision_time,
        state=state,
        available_bars=available_bars,
        required_bars=required_bars,
        reason=reason,
    )
