from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from tests.helpers import (
    create_rfq,
    iso,
    now_utc,
    quote_payload,
    rfq_payload,
    submit_quote,
)


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def minutes_between(start: str, end: str) -> float:
    return round((parse(end) - parse(start)).total_seconds() / 60, 2)


def activity_of(detail: dict, event_type: str) -> list[dict]:
    return [entry for entry in detail["activity"] if entry["eventType"] == event_type]


def test_create_list_and_envelope(client: TestClient) -> None:
    rfq = create_rfq(client)

    listed = client.get("/api/rfqs")
    body = listed.json()

    assert listed.status_code == 200
    assert body["success"] is True
    assert body["serverTime"].endswith("Z")
    assert len(body["data"]) == 1
    assert body["data"][0]["referenceId"] == "RFQ-TEST-1"
    assert body["data"][0]["status"] == "ACTIVE"
    assert body["data"][0]["lowestBid"] is None
    assert rfq["isBritishAuction"] is True


def test_schedule_validation_rejects_inverted_windows(client: TestClient) -> None:
    forced_before_close = rfq_payload(close_in_minutes=20, forced_in_minutes=10)
    response = client.post("/api/rfqs", json=forced_before_close)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    close_before_start = rfq_payload(start_in_minutes=10, close_in_minutes=5)
    response = client.post("/api/rfqs", json=close_before_start)
    assert response.status_code == 422


def test_duplicate_reference_is_rejected(client: TestClient) -> None:
    create_rfq(client)
    response = client.post("/api/rfqs", json=rfq_payload())
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_REFERENCE"


def test_unknown_rfq_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/rfqs/unknown")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RFQ_NOT_FOUND"


def test_quotes_are_ranked_by_total_cost(client: TestClient) -> None:
    rfq = create_rfq(client, british=False)

    first = submit_quote(client, rfq["id"], "Alpha", freight="280.00")
    assert first["data"]["rank"] == 1

    second = submit_quote(client, rfq["id"], "Bravo", freight="230.00")
    assert second["data"]["rank"] == 1

    third = submit_quote(client, rfq["id"], "Charlie", freight="180.00")
    assert third["data"]["rank"] == 1

    detail = client.get(f"/api/rfqs/{rfq['id']}").json()["data"]
    ranked = [(quote["carrierName"], quote["rank"]) for quote in detail["quotes"]]
    assert ranked == [("Charlie", 1), ("Bravo", 2), ("Alpha", 3)]
    assert detail["lowestBid"] == "200.00"
    assert detail["lowestCarrierName"] == "Charlie"
    assert detail["quoteCount"] == 3


def test_any_bid_extends_inside_window(client: TestClient) -> None:
    rfq = create_rfq(client, close_in_minutes=8, forced_in_minutes=120)

    result = submit_quote(client, rfq["id"], "Alpha")["data"]
    extension = result["extension"]

    assert extension["extended"] is True
    assert extension["trigger"] == "ANY_BID"
    assert extension["cappedByForcedClose"] is False
    assert minutes_between(extension["previousCloseTime"], extension["newCloseTime"]) == 5
    assert result["rfq"]["bidCloseTime"] == extension["newCloseTime"]

    detail = client.get(f"/api/rfqs/{rfq['id']}").json()["data"]
    extended_events = activity_of(detail, "AUCTION_EXTENDED")
    assert len(extended_events) == 1
    assert extended_events[0]["metadata"]["trigger"] == "ANY_BID"
    assert extended_events[0]["metadata"]["triggerWindowMins"] == 10


def test_no_extension_outside_window(client: TestClient) -> None:
    rfq = create_rfq(client, close_in_minutes=30, forced_in_minutes=120)

    result = submit_quote(client, rfq["id"], "Alpha")["data"]

    assert result["extension"]["extended"] is False
    assert result["rfq"]["bidCloseTime"] == rfq["bidCloseTime"]


def test_any_rank_change_trigger(client: TestClient) -> None:
    rfq = create_rfq(
        client,
        close_in_minutes=8,
        forced_in_minutes=180,
        trigger="ANY_RANK_CHANGE",
    )

    first = submit_quote(client, rfq["id"], "Alpha", freight="180.00")["data"]
    assert first["extension"]["extended"] is False

    second = submit_quote(client, rfq["id"], "Bravo", freight="230.00")["data"]
    assert second["extension"]["extended"] is False

    third = submit_quote(client, rfq["id"], "Charlie", freight="130.00")["data"]
    assert third["extension"]["extended"] is True
    assert third["extension"]["trigger"] == "ANY_RANK_CHANGE"
    assert "rankings changed" in third["extension"]["reason"].lower()

    detail = client.get(f"/api/rfqs/{rfq['id']}").json()["data"]
    assert len(activity_of(detail, "RANK_CHANGED")) == 1


def test_l1_change_trigger(client: TestClient) -> None:
    rfq = create_rfq(
        client,
        close_in_minutes=8,
        forced_in_minutes=180,
        trigger="L1_RANK_CHANGE",
        extension_mins=1,
    )

    first = submit_quote(client, rfq["id"], "Alpha", freight="180.00")["data"]
    assert first["extension"]["extended"] is True

    second = submit_quote(client, rfq["id"], "Bravo", freight="230.00")["data"]
    assert second["extension"]["extended"] is False

    third = submit_quote(client, rfq["id"], "Charlie", freight="130.00")["data"]
    assert third["extension"]["extended"] is True
    assert third["extension"]["trigger"] == "L1_RANK_CHANGE"


def test_extension_never_breaches_forced_close(client: TestClient) -> None:
    rfq = create_rfq(
        client,
        close_in_minutes=2,
        forced_in_minutes=4,
        window_mins=10,
        extension_mins=5,
        trigger="ANY_BID",
    )

    first = submit_quote(client, rfq["id"], "Alpha")["data"]
    assert first["extension"]["extended"] is True
    assert first["extension"]["cappedByForcedClose"] is True
    assert first["extension"]["newCloseTime"] == rfq["forcedCloseTime"]

    second = submit_quote(client, rfq["id"], "Bravo")["data"]
    assert second["extension"]["extended"] is False
    assert second["extension"]["cappedByForcedClose"] is True
    assert second["rfq"]["bidCloseTime"] == rfq["forcedCloseTime"]

    detail = client.get(f"/api/rfqs/{rfq['id']}").json()["data"]
    assert detail["bidCloseTime"] == detail["forcedCloseTime"]
    assert len(activity_of(detail, "EXTENSION_BLOCKED")) == 1


def test_british_auction_disabled_never_extends(client: TestClient) -> None:
    rfq = create_rfq(client, british=False, close_in_minutes=5)

    result = submit_quote(client, rfq["id"], "Alpha")["data"]

    assert result["extension"]["extended"] is False
    assert result["rfq"]["bidCloseTime"] == rfq["bidCloseTime"]


def test_bid_lifecycle_guards(client: TestClient) -> None:
    scheduled = create_rfq(
        client,
        reference="RFQ-SCHEDULED",
        start_in_minutes=60,
        close_in_minutes=120,
        forced_in_minutes=180,
    )
    assert scheduled["status"] == "SCHEDULED"
    response = client.post(
        f"/api/rfqs/{scheduled['id']}/quotes", json=quote_payload("Alpha")
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BIDDING_NOT_OPEN"

    closed = create_rfq(
        client,
        reference="RFQ-CLOSED",
        start_in_minutes=-120,
        close_in_minutes=-60,
        forced_in_minutes=60,
    )
    assert closed["status"] == "CLOSED"
    response = client.post(
        f"/api/rfqs/{closed['id']}/quotes", json=quote_payload("Alpha")
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AUCTION_CLOSED"

    forced = create_rfq(
        client,
        reference="RFQ-FORCED",
        start_in_minutes=-120,
        close_in_minutes=-90,
        forced_in_minutes=-30,
    )
    assert forced["status"] == "FORCE_CLOSED"
    response = client.post(
        f"/api/rfqs/{forced['id']}/quotes", json=quote_payload("Alpha")
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AUCTION_FORCE_CLOSED"


def test_expired_quote_validity_is_rejected(client: TestClient) -> None:
    rfq = create_rfq(client)

    response = client.post(
        f"/api/rfqs/{rfq['id']}/quotes",
        json=quote_payload(
            "Alpha", validity_override=iso(now_utc() - timedelta(days=1))
        ),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_QUOTE_VALIDITY"
