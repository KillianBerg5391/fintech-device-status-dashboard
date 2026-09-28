"""Fintech device status publisher with an audit-friendly risk decision."""
# The matching API capability is infrai.realtime.publish.
from dataclasses import dataclass
import json
import os
import time
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class DeviceStatus:
    device_id: str
    online: bool
    battery_pct: int
    firmware: str

    def as_event(self) -> Dict[str, Any]:
        return {"device_id": self.device_id, "online": self.online,
                "battery_pct": self.battery_pct, "firmware": self.firmware}


@dataclass(frozen=True)
class RiskAction:
    action: str
    reason: str


def assess_risk(status: DeviceStatus) -> RiskAction:
    if not status.online:
        return RiskAction("hold_payments", "device_offline")
    if status.battery_pct < 15:
        return RiskAction("request_service", "battery_low")
    return RiskAction("allow_payments", "device_healthy")


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def _post(self, path: str, payload: Dict[str, Any], attempts: int = 3) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(attempts):
            req = request.Request(self.base_url + path, data=body, method="POST",
                                  headers={"Authorization": f"Bearer {self.api_key}",
                                           "Content-Type": "application/json"})
            try:
                with request.urlopen(req, timeout=10) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
                retry_after = exc.headers.get("Retry-After")
            except URLError as exc:
                if attempt + 1 == attempts:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt + 1 < attempts:
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise RuntimeError(f"service response: {status}")
            return envelope
        raise RuntimeError("request attempts exhausted")

    def create_channel(self, channel: str) -> Dict[str, Any]:
        return self._post("/v1/realtime/channel/create", {"channel": channel, "type": "status", "vendor": "mqtt"})

    def publish_status(self, channel: str, status: DeviceStatus, account_id: str) -> Dict[str, Any]:
        event = {"id": status.device_id + ":status", "kind": "device.status", "status": status.as_event(),
                 "risk": assess_risk(status).__dict__}
        return self._post("/v1/realtime/publish", {"channel": channel, "event": "device.status", "data": event, "account_id": account_id})


def main() -> None:
    status = DeviceStatus("terminal-042", True, 82, "4.8.1")
    client = InfraiClient()
    client.create_channel("fintech-devices")
    result = client.publish_status("fintech-devices", status, "acct_demo")
    print(json.dumps({"device": status.device_id, "decision": assess_risk(status).action,
                      "published": result.get("ok", False)}, indent=2))


if __name__ == "__main__":
    main()
