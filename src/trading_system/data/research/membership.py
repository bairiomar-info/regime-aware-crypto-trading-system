"""Deterministic construction of point-in-time membership intervals."""

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import MembershipStatus, PointInTimeMembership


class MembershipEvent(BaseModel):
    """A historical membership state change admissible for PIT research."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    instrument_id: str = Field(min_length=1)
    effective_at: object
    status: MembershipStatus
    source: str = Field(min_length=1)
    source_available_at: object | None = None

    @field_validator("effective_at", "source_available_at")
    @classmethod
    def require_datetime(cls, value):
        from datetime import UTC, datetime

        if value is None:
            return None
        if not isinstance(value, datetime):
            raise TypeError("membership event timestamps must be datetimes")
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("membership event timestamps must be UTC-aware")
        return value

    @model_validator(mode="after")
    def validate_availability(self):
        if (
            self.source_available_at is not None
            and self.source_available_at > self.effective_at
        ):
            raise ValueError("source_available_at cannot be after effective_at")
        return self


def build_membership_intervals(
    events: Iterable[MembershipEvent],
) -> tuple[PointInTimeMembership, ...]:
    """Build deterministic half-open membership intervals from state events.

    Events are ordered by instrument, effective time, and stable event content.
    Two different states at the same effective time are rejected because there
    is no defensible deterministic choice between conflicting evidence.
    Repeated identical states are collapsed as redundant observations.
    """
    ordered = sorted(
        events,
        key=lambda event: (
            event.instrument_id,
            event.effective_at,
            event.status.value,
            event.source,
        ),
    )

    intervals: list[PointInTimeMembership] = []
    by_instrument: dict[str, list[MembershipEvent]] = {}
    for event in ordered:
        by_instrument.setdefault(event.instrument_id, []).append(event)

    for instrument_id, instrument_events in by_instrument.items():
        compacted: list[MembershipEvent] = []
        for event in instrument_events:
            if compacted and event.effective_at == compacted[-1].effective_at:
                previous = compacted[-1]
                if event.status != previous.status:
                    raise ValueError(
                        f"conflicting membership states at {instrument_id} "
                        f"and {event.effective_at.isoformat()}"
                    )
                # Same state at the same time is redundant. Keep the
                # lexicographically first source for deterministic provenance.
                continue
            compacted.append(event)

        for index, event in enumerate(compacted):
            effective_to = (
                compacted[index + 1].effective_at
                if index + 1 < len(compacted)
                else None
            )
            intervals.append(
                PointInTimeMembership(
                    instrument_id=instrument_id,
                    effective_from=event.effective_at,
                    effective_to=effective_to,
                    status=event.status,
                    source=event.source,
                    source_available_at=event.source_available_at,
                )
            )

    return tuple(intervals)


def membership_at(
    intervals: Iterable[PointInTimeMembership],
    *,
    instrument_id: str,
    decision_time,
) -> PointInTimeMembership | None:
    """Return the interval containing ``decision_time`` for an instrument."""
    matches = [
        interval
        for interval in intervals
        if interval.instrument_id == instrument_id
        and interval.effective_from <= decision_time
        and (interval.effective_to is None or decision_time < interval.effective_to)
    ]
    if len(matches) > 1:
        raise ValueError(f"overlapping membership intervals for {instrument_id}")
    return matches[0] if matches else None
