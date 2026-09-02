from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from trading_system.data.research import (
    EligibilityReason,
    MembershipStatus,
    PointInTimeMembership,
    ResearchDatasetManifest,
    UniversePolicy,
    evaluate_eligibility,
)


T0 = datetime(2025, 1, 1, tzinfo=UTC)
T1 = datetime(2025, 2, 1, tzinfo=UTC)
T2 = datetime(2025, 3, 1, tzinfo=UTC)


def policy(**overrides) -> UniversePolicy:
    values = {
        "policy_id": "spot-research",
        "version": "v1.0.0",
        "minimum_history_bars": 10,
        "minimum_quote_volume": "1000",
        "excluded_classifications": ("stablecoin", "leveraged"),
    }
    values.update(overrides)
    return UniversePolicy(**values)


def test_membership_interval_is_immutable_and_utc():
    membership = PointInTimeMembership(
        instrument_id="BINANCE:BTCUSDT",
        effective_from=T0,
        effective_to=T2,
        status=MembershipStatus.TRADABLE,
        source="binance",
        source_available_at=T0,
    )

    assert membership.instrument_id == "BINANCE:BTCUSDT"
    with pytest.raises(ValidationError):
        membership.instrument_id = "BINANCE:ETHUSDT"


def test_membership_rejects_future_source_information():
    with pytest.raises(ValidationError, match="source_available_at"):
        PointInTimeMembership(
            instrument_id="BINANCE:BTCUSDT",
            effective_from=T0,
            status=MembershipStatus.TRADABLE,
            source="binance",
            source_available_at=T1,
        )


def test_pre_listing_instrument_is_excluded():
    decision = evaluate_eligibility(
        instrument_id="BINANCE:NEWUSDT",
        decision_time=T0,
        policy=policy(minimum_history_bars=0, minimum_quote_volume=None),
        membership_status=MembershipStatus.NOT_LISTED,
        market_type="spot",
        quote_asset="USDT",
        history_bars=100,
    )

    assert not decision.eligible
    assert decision.reasons == (EligibilityReason.NOT_LISTED,)


def test_delisted_instrument_remains_historically_represented_but_is_ineligible_after_delisting():
    decision = evaluate_eligibility(
        instrument_id="BINANCE:OLDUSDT",
        decision_time=T2,
        policy=policy(minimum_history_bars=0, minimum_quote_volume=None),
        membership_status=MembershipStatus.DELISTED,
        market_type="spot",
        quote_asset="USDT",
        history_bars=100,
    )

    assert not decision.eligible
    assert EligibilityReason.DELISTED in decision.reasons


def test_insufficient_history_has_explicit_reason():
    decision = evaluate_eligibility(
        instrument_id="BINANCE:NEWUSDT",
        decision_time=T1,
        policy=policy(minimum_quote_volume=None),
        membership_status=MembershipStatus.TRADABLE,
        market_type="spot",
        quote_asset="USDT",
        history_bars=9,
    )

    assert not decision.eligible
    assert EligibilityReason.INSUFFICIENT_HISTORY in decision.reasons


def test_low_liquidity_has_explicit_reason():
    decision = evaluate_eligibility(
        instrument_id="BINANCE:THINUSDT",
        decision_time=T1,
        policy=policy(minimum_history_bars=0),
        membership_status=MembershipStatus.TRADABLE,
        market_type="spot",
        quote_asset="USDT",
        history_bars=100,
        quote_volume=Decimal("999.99"),
    )

    assert not decision.eligible
    assert EligibilityReason.INSUFFICIENT_LIQUIDITY in decision.reasons


def test_classification_exclusion_is_explicit():
    decision = evaluate_eligibility(
        instrument_id="BINANCE:STABLEUSDT",
        decision_time=T1,
        policy=policy(minimum_history_bars=0, minimum_quote_volume=None),
        membership_status=MembershipStatus.TRADABLE,
        market_type="spot",
        quote_asset="USDT",
        history_bars=100,
        classification="stablecoin",
    )

    assert not decision.eligible
    assert decision.reasons == (EligibilityReason.EXCLUDED_CLASSIFICATION,)


def test_future_information_can_never_make_a_past_decision_eligible():
    decision = evaluate_eligibility(
        instrument_id="BINANCE:BTCUSDT",
        decision_time=T0,
        policy=policy(minimum_history_bars=0, minimum_quote_volume=None),
        membership_status=MembershipStatus.TRADABLE,
        market_type="spot",
        quote_asset="USDT",
        history_bars=100,
        evidence_available_at=T1,
    )

    assert not decision.eligible
    assert decision.reasons == (EligibilityReason.FUTURE_INFORMATION,)


def test_eligible_decision_has_single_canonical_reason():
    decision = evaluate_eligibility(
        instrument_id="BINANCE:BTCUSDT",
        decision_time=T1,
        policy=policy(minimum_history_bars=10, minimum_quote_volume="1000"),
        membership_status=MembershipStatus.TRADABLE,
        market_type="spot",
        quote_asset="USDT",
        history_bars=100,
        quote_volume=Decimal("1000000"),
    )

    assert decision.eligible
    assert decision.reasons == (EligibilityReason.ELIGIBLE,)


def test_wrong_market_and_quote_asset_are_excluded():
    decision = evaluate_eligibility(
        instrument_id="BINANCE:BTCUSDC",
        decision_time=T1,
        policy=policy(minimum_history_bars=0, minimum_quote_volume=None),
        membership_status=MembershipStatus.TRADABLE,
        market_type="margin",
        quote_asset="USDC",
        history_bars=100,
    )

    assert not decision.eligible
    assert EligibilityReason.WRONG_MARKET_TYPE in decision.reasons
    assert EligibilityReason.DISALLOWED_QUOTE_ASSET in decision.reasons


def test_research_manifest_is_versioned_and_immutable():
    manifest = ResearchDatasetManifest(
        research_dataset_id="spot-pit",
        research_dataset_version="v1.0.0",
        canonical_dataset_id="spot_ohlcv",
        canonical_dataset_version="v1.0.0",
        universe_policy_id="spot-research",
        universe_policy_version="v1.0.0",
        start_time=T0,
        end_time=T2,
        decision_frequency="1d",
        code_commit="abc123",
        membership_count=42,
    )

    assert manifest.membership_count == 42
    with pytest.raises(ValidationError):
        manifest.membership_count = 43


def test_research_manifest_rejects_invalid_bounds():
    with pytest.raises(ValidationError, match="end_time"):
        ResearchDatasetManifest(
            research_dataset_id="spot-pit",
            research_dataset_version="v1.0.0",
            canonical_dataset_id="spot_ohlcv",
            canonical_dataset_version="v1.0.0",
            universe_policy_id="spot-research",
            universe_policy_version="v1.0.0",
            start_time=T2,
            end_time=T1,
            decision_frequency="1d",
            membership_count=0,
        )
