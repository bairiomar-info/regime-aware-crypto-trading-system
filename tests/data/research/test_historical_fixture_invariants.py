from datetime import UTC, datetime, timedelta
from decimal import Decimal

from trading_system.data.research import (
    EligibilityReason,
    MembershipEvent,
    MembershipStatus,
    UniversePolicy,
    build_membership_intervals,
    evaluate_eligibility,
    membership_at,
    rolling_quote_volume,
)

T0 = datetime(2026, 1, 1, tzinfo=UTC)
T1 = T0 + timedelta(hours=1)
T2 = T0 + timedelta(hours=2)


def test_fixture_membership_and_eligibility_are_point_in_time():
    intervals = build_membership_intervals(
        [
            MembershipEvent(
                instrument_id="BINANCE:AAAUSDT",
                effective_at=T0,
                status=MembershipStatus.TRADABLE,
                source="fixture",
                source_available_at=T0,
            ),
            MembershipEvent(
                instrument_id="BINANCE:AAAUSDT",
                effective_at=T2,
                status=MembershipStatus.DELISTED,
                source="fixture",
                source_available_at=T2,
            ),
        ]
    )
    policy = UniversePolicy(policy_id="fixture", version="1.0.0", minimum_history_bars=2)

    membership = membership_at(intervals, instrument_id="BINANCE:AAAUSDT", decision_time=T1)
    assert membership is not None
    assert membership.status == MembershipStatus.TRADABLE

    decision = evaluate_eligibility(
        instrument_id="BINANCE:AAAUSDT",
        decision_time=T1,
        policy=policy,
        membership_status=membership.status,
        market_type="spot",
        quote_asset="USDT",
        history_bars=2,
        quote_volume=Decimal("1000"),
        evidence_available_at=T1,
    )
    assert decision.eligible is True


def test_fixture_future_membership_cannot_enter_an_earlier_decision():
    intervals = build_membership_intervals(
        [
            MembershipEvent(
                instrument_id="BINANCE:NEWUSDT",
                effective_at=T1,
                status=MembershipStatus.TRADABLE,
                source="fixture",
                source_available_at=T1,
            )
        ]
    )
    assert membership_at(intervals, instrument_id="BINANCE:NEWUSDT", decision_time=T0) is None

    policy = UniversePolicy(policy_id="fixture", version="1.0.0")
    decision = evaluate_eligibility(
        instrument_id="BINANCE:NEWUSDT",
        decision_time=T0,
        policy=policy,
        membership_status=MembershipStatus.NOT_LISTED,
        market_type="spot",
        quote_asset="USDT",
        history_bars=100,
        evidence_available_at=T1,
    )
    assert decision.eligible is False
    assert decision.reasons == (EligibilityReason.FUTURE_INFORMATION,)


def test_fixture_liquidity_is_as_of_window_only():
    typical, coverage, sufficient = rolling_quote_volume(
        ["100", "120", "10000"],
        lookback_bars=3,
        minimum_quote_volume="110",
    )
    assert typical == Decimal("120")
    assert coverage == Decimal("1")
    assert sufficient is True
