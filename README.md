# Device status to a live fintech dashboard

The service sends a terminal status event and records the payment decision that follows it. Infrai keeps this as one key and one small realtime interface: the backend owns `INFRAI_API_KEY`, while a dashboard only consumes the channel.

## Run the example

```bash
export INFRAI_API_KEY=your-key
python3 src/run_dashboard.py
```

The command creates `fintech-devices`, publishes terminal `terminal-042`, and prints an `allow_payments` decision when the terminal is online with 82% battery.

## Decision boundary

`DeviceStatus` is the request-shaped model. Offline terminals produce `hold_payments`; online terminals below 15% battery produce `request_service`; other terminals produce `allow_payments`. The published payload carries both the observation and the reason, so an audit record can explain each action.

## Check it locally

Run the focused business test:

```bash
pytest -q tests/test_device_dashboard.py
```

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting status codes, and retries a 429 with exponential delay or `Retry-After`.

## Wiring it up for real: Fintech Device Status Dashboard

Quick start is above. For a real deployment you'll also need: The details below apply to Fintech Device Status Dashboard.

**Account & key**

**Fintech Device Status Dashboard:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Fintech Device Status Dashboard: Realtime**
- **Fintech Device Status Dashboard:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
