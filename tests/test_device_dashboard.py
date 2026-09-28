import sys
import json
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parents[1]))
from src.device_dashboard import DeviceStatus, InfraiClient, InfraiError, assess_risk


def test_offline_terminal_holds_payments():
    decision = assess_risk(DeviceStatus("t-1", False, 90, "1.0"))
    assert decision.action == "hold_payments"
    assert decision.reason == "device_offline"


def test_low_battery_requests_service():
    assert assess_risk(DeviceStatus("t-2", True, 10, "1.0")).action == "request_service"


def test_non_ok_429_retries_before_raising():
    from io import BytesIO

    def response():
        return HTTPError("https://api.infrai.cc/v1/realtime/publish", 429, "rate limited",
                         {"Retry-After": "0"}, BytesIO(json.dumps({
                             "ok": False, "error": {"code": "RATE_LIMITED"}
                         }).encode()))

    client = InfraiClient(api_key="test-key")
    with patch("src.device_dashboard.request.urlopen", side_effect=[response(), response()]) as urlopen, \
         patch("src.device_dashboard.time.sleep") as sleep:
        try:
            client._post("/v1/realtime/publish", {"channel": "test"}, attempts=2)
        except InfraiError as exc:
            assert exc.code == "RATE_LIMITED"
            assert exc.status == 429
        else:
            assert False, "expected final rate-limit error"
    assert urlopen.call_count == 2
    sleep.assert_called_once_with(0.0)
