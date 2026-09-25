from backend.live_service import normalize_manager_chip_state


def test_first_half_chip_use_only_consumes_the_first_set():
    state = normalize_manager_chip_state(3, {
        "chips": [
            {"name": "bboost", "event": 2},
            {"name": "wildcard", "event": 22},
        ],
    })

    assert state["known"] is True
    assert state["period"] == 1
    assert state["bench_boost_available"] is False
    assert state["wildcard_available"] is True
    assert state["used_in_period"] == [{"chip": "BENCH_BOOST", "event": 2}]


def test_second_half_uses_the_refreshed_chip_set():
    state = normalize_manager_chip_state(23, {
        "chips": [
            {"name": "wildcard", "event": 7},
            {"name": "wildcard", "event": 22},
        ],
    })

    assert state["period"] == 2
    assert state["wildcard_available"] is False
    assert state["bench_boost_available"] is True


def test_unknown_chip_history_is_conservative():
    state = normalize_manager_chip_state(3, {})
    assert state["known"] is False
    assert state["wildcard_available"] is False
    assert state["free_hit_available"] is False
    assert state["bench_boost_available"] is False
    assert state["triple_captain_available"] is False
