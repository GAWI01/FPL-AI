from backend.fpl_gateway import FplGateway, begin_gateway_trace, end_gateway_trace
from concurrent.futures import ThreadPoolExecutor
from threading import Event


class Response:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"events": [{"id": 2}]}


def test_gateway_coalesces_fresh_reads():
    calls = []
    gateway = FplGateway(
        http_get=lambda *args, **kwargs: calls.append(args[0]) or Response(),
        clock=lambda: 100.0,
    )

    first = gateway.get_json("bootstrap-static/", ttl_seconds=300)
    second = gateway.get_json("bootstrap-static/", ttl_seconds=300)

    assert first.data == second.data
    assert first.stale is False
    assert calls == ["https://fantasy.premierleague.com/api/bootstrap-static/"]


def test_gateway_returns_last_good_value_as_stale_after_network_error():
    state = {"fail": False}

    def get(*args, **kwargs):
        if state["fail"]:
            raise OSError("offline")
        return Response()

    now = {"value": 100.0}
    gateway = FplGateway(http_get=get, clock=lambda: now["value"])
    gateway.get_json("bootstrap-static/", ttl_seconds=1)

    state["fail"] = True
    now["value"] = 102.0
    result = gateway.get_json("bootstrap-static/", ttl_seconds=1)

    assert result.stale is True
    assert result.data == {"events": [{"id": 2}]}


def test_gateway_accepts_full_official_api_urls():
    calls = []
    gateway = FplGateway(
        http_get=lambda *args, **kwargs: calls.append(args[0]) or Response(),
        clock=lambda: 100.0,
    )

    gateway.get_json(
        "https://fantasy.premierleague.com/api/entry/7/",
        ttl_seconds=60,
    )

    assert calls == ["https://fantasy.premierleague.com/api/entry/7/"]


def test_gateway_trace_preserves_real_freshness_and_stale_state():
    state = {"fail": False}
    now = {"value": 100.0}

    def get(*args, **kwargs):
        if state["fail"]:
            raise OSError("offline")
        return Response()

    gateway = FplGateway(http_get=get, clock=lambda: now["value"])
    gateway.get_json("bootstrap-static/", ttl_seconds=1)
    state["fail"] = True
    now["value"] = 102.0

    token = begin_gateway_trace()
    gateway.get_json("bootstrap-static/", ttl_seconds=1)
    trace = end_gateway_trace(token)

    assert len(trace) == 1
    assert trace[0].stale is True
    assert trace[0].fetched_at.tzinfo is not None


def test_gateway_retries_once_after_a_transient_network_error():
    calls = []

    def get(*args, **kwargs):
        calls.append(args[0])
        if len(calls) == 1:
            raise OSError("temporary outage")
        return Response()

    gateway = FplGateway(http_get=get, clock=lambda: 100.0)
    result = gateway.get_json("bootstrap-static/", ttl_seconds=300)

    assert result.stale is False
    assert result.data == {"events": [{"id": 2}]}
    assert len(calls) == 2


def test_slow_request_does_not_serialize_unrelated_official_paths():
    first_started = Event()
    second_started = Event()
    release_first = Event()

    def get(url, **kwargs):
        if url.endswith("/first/"):
            first_started.set()
            release_first.wait(timeout=2)
        else:
            second_started.set()
        return Response()

    gateway = FplGateway(http_get=get, clock=lambda: 100.0)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(gateway.get_json, "first/", 0)
        assert first_started.wait(timeout=1)
        second = pool.submit(gateway.get_json, "second/", 0)
        assert second_started.wait(timeout=1)
        release_first.set()
        first.result(timeout=1)
        second.result(timeout=1)
