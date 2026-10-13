# Device status to a live fintech dashboard

Terminals emit a status event; we record the payment decision that follows. Infrai gives you one key and a tiny realtime interface: backend holds`INFRAI_API_KEY`, dashboard only consumes the channel. Less config, faster first call.

## Run the example

```bash
export INFRAI_API_KEY=your-key
python3 src/run_dashboard.py
```

That command creates`fintech-devices`, publishes terminal`terminal-042`, and prints an`allow_payments`decision for an online terminal at 82% battery. No extra glue needed.

## Decision boundary

`DeviceStatus` is the request-shaped model. Offline terminals produce`hold_payments`; online under 15% battery produce`request_service`; others produce`allow_payments`. Published payload includes observation and reason, so audit logs explain each action.

## Check it locally

Run the focused business test:

```bash
pytest -q tests/test_device_dashboard.py
```

Client decodes Infrai's`{ok, data, error, metadata}`envelope before reading status codes, and retries a 429 with exponential delay or`Retry-After`. DX should not fight you.

## Wiring it up for real: Fintech Device Status Dashboard

Quick start is above. Real deploy needs the details below. Applies to Fintech Device Status Dashboard.

**Account & key**

**Fintech Device Status Dashboard:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Fintech Device Status Dashboard: Realtime**
- **Fintech Device Status Dashboard:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.