from trading_system.regime.hysteresis import HysteresisConfig, update_hysteresis


def test_candidate_switch_resets_confirmation_count():
    first = update_hysteresis(
        "UP", "NEUTRAL", confirmation_count=0, previous_candidate_state=None,
        state_age=3, config=HysteresisConfig(confirmation_bars=2),
    )
    assert first.state == "UP"
    assert first.candidate_state == "NEUTRAL"
    assert first.confirmation_count == 1

    switched = update_hysteresis(
        first.state, "DOWN", confirmation_count=first.confirmation_count,
        previous_candidate_state=first.candidate_state, state_age=first.state_age,
        config=HysteresisConfig(confirmation_bars=2),
    )
    assert switched.state == "UP"
    assert switched.candidate_state == "DOWN"
    assert switched.confirmation_count == 1


def test_same_candidate_reaches_confirmation_after_consecutive_observations():
    first = update_hysteresis(
        "UP", "DOWN", state_age=3, config=HysteresisConfig(confirmation_bars=2),
    )
    second = update_hysteresis(
        first.state, "DOWN", confirmation_count=first.confirmation_count,
        previous_candidate_state=first.candidate_state, state_age=first.state_age,
        config=HysteresisConfig(confirmation_bars=2),
    )
    assert first.confirmation_count == 1
    assert second.state == "DOWN"
    assert second.candidate_state is None
    assert second.confirmation_count == 0
    assert second.state_age == 1


def test_return_to_accepted_state_clears_pending_candidate():
    pending = update_hysteresis(
        "UP", "DOWN", state_age=3, config=HysteresisConfig(confirmation_bars=3),
    )
    recovered = update_hysteresis(
        pending.state, "UP", confirmation_count=pending.confirmation_count,
        previous_candidate_state=pending.candidate_state, state_age=pending.state_age,
        config=HysteresisConfig(confirmation_bars=3),
    )
    assert recovered.state == "UP"
    assert recovered.candidate_state is None
    assert recovered.confirmation_count == 0
