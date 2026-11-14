from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(value: datetime) -> str:
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def rfq_payload(
    *,
    reference: str = "RFQ-TEST-1",
    start_in_minutes: float = -30,
    close_in_minutes: float = 30,
    forced_in_minutes: float = 120,
    trigger: str = "ANY_BID",
    window_mins: int = 10,
    extension_mins: int = 5,
    british: bool = True,
) -> dict[str, object]:
    base = now_utc()
    return {
        "referenceId": reference,
        "title": "Test lane",
        "pickupDate": iso(base + timedelta(days=7)),
        "bidStartTime": iso(base + timedelta(minutes=start_in_minutes)),
        "bidCloseTime": iso(base + timedelta(minutes=close_in_minutes)),
        "forcedCloseTime": iso(base + timedelta(minutes=forced_in_minutes)),
        "isBritishAuction": british,
        "triggerWindowMins": window_mins,
        "extensionDurationMins": extension_mins,
        "extensionTrigger": trigger,
    }


def create_rfq(client: TestClient, **overrides: object) -> dict:
    response = client.post("/api/rfqs", json=rfq_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()["data"]


def quote_payload(
    carrier: str,
    *,
    freight: str = "100.00",
    origin: str = "10.00",
    destination: str = "10.00",
    transit: int = 10,
    validity_days: int = 10,
    validity_override: str | None = None,
) -> dict[str, object]:
    return {
        "carrierName": carrier,
        "freightCharges": freight,
        "originCharges": origin,
        "destinationCharges": destination,
        "transitTimeDays": transit,
        "validityDate": validity_override
        or iso(now_utc() + timedelta(days=validity_days)),
    }


def submit_quote(
    client: TestClient,
    rfq_id: str,
    carrier: str,
    **overrides: object,
) -> dict:
    response = client.post(
        f"/api/rfqs/{rfq_id}/quotes", json=quote_payload(carrier, **overrides)
    )
    return response.json()
