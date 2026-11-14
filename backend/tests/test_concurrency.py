from __future__ import annotations

import threading
from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import iso, now_utc, quote_payload


CARRIERS = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot"]


def test_parallel_final_window_bids_are_serialised(client: TestClient) -> None:
    base = now_utc()
    payload = {
        "referenceId": "RFQ-CONCURRENT",
        "title": "Concurrent final minute",
        "pickupDate": iso(base + timedelta(days=5)),
        "bidStartTime": iso(base - timedelta(minutes=30)),
        "bidCloseTime": iso(base + timedelta(seconds=10)),
        "forcedCloseTime": iso(base + timedelta(minutes=5)),
        "isBritishAuction": True,
        "triggerWindowMins": 10,
        "extensionDurationMins": 1,
        "extensionTrigger": "ANY_BID",
    }
    created = client.post("/api/rfqs", json=payload)
    assert created.status_code == 201, created.text
    rfq_id = created.json()["data"]["id"]
    forced_close = created.json()["data"]["forcedCloseTime"]

    results: list[int] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def bid(carrier: str) -> None:
        try:
            thread_client = TestClient(app)
            response = thread_client.post(
                f"/api/rfqs/{rfq_id}/quotes", json=quote_payload(carrier)
            )
            with lock:
                results.append(response.status_code)
        except BaseException as exc:  # noqa: BLE001
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=bid, args=(carrier,)) for carrier in CARRIERS]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert not errors, errors
    assert results == [201] * len(CARRIERS)

    detail = client.get(f"/api/rfqs/{rfq_id}").json()["data"]

    assert detail["quoteCount"] == len(CARRIERS)
    assert detail["bidCloseTime"] <= forced_close
    assert detail["bidCloseTime"] == forced_close

    ranks = sorted(quote["rank"] for quote in detail["quotes"])
    assert ranks == list(range(1, len(CARRIERS) + 1))

    extensions = [
        entry for entry in detail["activity"] if entry["eventType"] == "AUCTION_EXTENDED"
    ]
    blocked = [
        entry
        for entry in detail["activity"]
        if entry["eventType"] == "EXTENSION_BLOCKED"
    ]
    assert len(extensions) == 5
    assert len(blocked) == 1

    for entry in extensions:
        assert entry["metadata"]["newCloseTime"] <= forced_close

    close_times = [entry["metadata"]["newCloseTime"] for entry in extensions]
    assert close_times == sorted(close_times, reverse=True)


def test_concurrent_bids_never_lose_quotes(client: TestClient) -> None:
    created = client.post(
        "/api/rfqs",
        json={
            "referenceId": "RFQ-CONCURRENT-2",
            "title": "Concurrent volume",
            "pickupDate": iso(now_utc() + timedelta(days=5)),
            "bidStartTime": iso(now_utc() - timedelta(minutes=30)),
            "bidCloseTime": iso(now_utc() + timedelta(minutes=30)),
            "forcedCloseTime": iso(now_utc() + timedelta(minutes=120)),
            "isBritishAuction": False,
            "triggerWindowMins": 10,
            "extensionDurationMins": 5,
            "extensionTrigger": "ANY_BID",
        },
    )
    rfq_id = created.json()["data"]["id"]

    carriers = [f"Carrier-{index:02d}" for index in range(12)]
    errors: list[BaseException] = []
    lock = threading.Lock()

    def bid(carrier: str, freight: str) -> None:
        try:
            thread_client = TestClient(app)
            thread_client.post(
                f"/api/rfqs/{rfq_id}/quotes",
                json=quote_payload(carrier, freight=freight),
            )
        except BaseException as exc:  # noqa: BLE001
            with lock:
                errors.append(exc)

    threads = [
        threading.Thread(
            target=bid, args=(carrier, f"{100 + index * 5}.00")
        )
        for index, carrier in enumerate(carriers)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert not errors, errors

    detail = client.get(f"/api/rfqs/{rfq_id}").json()["data"]
    assert detail["quoteCount"] == len(carriers)
    assert sorted(quote["rank"] for quote in detail["quotes"]) == list(
        range(1, len(carriers) + 1)
    )
