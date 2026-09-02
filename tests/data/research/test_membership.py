from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from trading_system.data.research import (
    MembershipEvent,
    MembershipStatus,
    build_membership_intervals,
    membership_at,
)


T0 = datetime(2025, 1, 1, tzinfo=UTC)
T1 = datetime(2025, 2, 1, tzinfo=UTC)
T2 = datetime(2025, 3, 1, tzinfo=UTC)


def event(instrument_id, effective_at, status, source="binance"):
    return MembershipEvent(
        instrument_id=instrument_id,
        effective_at=effective_at,
        status=status,
        source=source,
        source_available_at=effective_at,
    )


def test_events_become_half_open_intervals():
    intervals = build_membership_intervals(
        [
            event("BINANCE:BTCUSDT", T1, MembershipStatus.TRADABLE),
            event("BINANCE:BTCUSDT", T2, MembershipStatus.DELISTED),
        ]
    )

    assert len(intervals) == 2
    assert intervals[0].effective_from == T1
    assert intervals[0].effective_to == T2
    assert intervals[0].status == MembershipStatus.TRADABLE
    assert intervals[1].effective_from == T2
    assert intervals[1].effective_to is None
    assert intervals[1].status == MembershipStatus.DELISTED


def test_membership_lookup_respects_boundaries():
    intervals = build_membership_intervals(
        [
            event("BINANCE:BTCUSDT", T0, MembershipStatus.TRADABLE),
            event("BINANCE:BTCUSDT", T1, MembershipStatus.HALTED),
        ]
    )

    assert membership_at(intervals, instrument_id="BINANCE:BTCUSDT", decision_time=T0).status == MembershipStatus.TRADABLE
    assert membership_at(intervals, instrument_id="BINANCE:BTCUSDT", decision_time=T1).status == MembershipStatus.HALTED
    assert membership_at(intervals, instrument_id="BINANCE:ETHUSDT", decision_time=T1) is None


def test_events_are_deterministically_ordered_by_instrument_and_time():
    events = [
        event("BINANCE:ETHUSDT", T1, MembershipStatus.TRADABLE),
        event("BINANCE:BTCUSDT", T2, MembershipStatus.DELISTED),
        event("BINANCE:BTCUSDT", T0, MembershipStatus.TRADABLE),
    ]

    intervals = build_membership_intervals(events)

    assert [(item.instrument_id, item.effective_from) for item in intervals] == [
        ("BINANCE:BTCUSDT", T0),
        ("BINANCE:BTCUSDT", T2),
        ("BINANCE:ETHUSDT", T1),
    ]


def test_identical_same_time_events_are_collapsed():
    intervals = build_membership_intervals(
        [
            event("BINANCE:BTCUSDT", T0, MembershipStatus.TRADABLE, "binance-a"),
            event("BINANCE:BTCUSDT", T0, MembershipStatus.TRADABLE, "binance-b"),
        ]
    )

    assert len(intervals) == 1
    assert intervals[0].source == "binance-a"


def test_conflicting_same_time_states_are_rejected():
    with pytest.raises(ValueError, match="conflicting membership states"):
        build_membership_intervals(
            [
                event("BINANCE:BTCUSDT", T0, MembershipStatus.TRADABLE),
                event("BINANCE:BTCUSDT", T0, MembershipStatus.HALTED),
            ]
        )


def test_future_source_information_is_rejected():
    with pytest.raises(ValidationError, match="source_available_at"):
        MembershipEvent(
            instrument_id="BINANCE:BTCUSDT",
            effective_at=T0,
            status=MembershipStatus.TRADABLE,
            source="binance",
            source_available_at=T1,
        )


def test_membership_event_requires_utc():
    with pytest.raises(ValidationError, match="UTC-aware"):
        MembershipEvent(
            instrument_id="BINANCE:BTCUSDT",
            effective_at=datetime(2025, 1, 1),
            status=MembershipStatus.TRADABLE,
            source="binance",
        )


def test_membership_lookup_rejects_overlapping_intervals():
    first = event("BINANCE:BTCUSDT", T0, MembershipStatus.TRADABLE)
    second = event("BINANCE:BTCUSDT", T2, MembershipStatus.DELISTED)
    overlapping = event("BINANCE:BTCUSDT", T1, MembershipStatus.HALTED)

    with pytest.raises(ValueError, match="overlapping"):
        membership_at(
            [
                build_membership_intervals([first, overlapping, second])[0],
                build_membership_intervals([first, second])[0],
            ],
            instrument_id="BINANCE:BTCUSDT",
            decision_time=T1,
        )
