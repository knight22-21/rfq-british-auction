from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.domain import TriggerType
from app.services.extension import (
    QuoteSnapshot,
    in_trigger_window,
    next_close_time,
    rank_quotes,
    ranks_changed,
    trigger_fired,
)

T0 = datetime(2026, 1, 1, 12, 0, 0)


def snapshot(quote_id: str, carrier: str, total: str, offset_minutes: int = 0):
    return QuoteSnapshot(
        quote_id=quote_id,
        carrier_name=carrier,
        total_amount=Decimal(total),
        submitted_at=T0 + timedelta(minutes=offset_minutes),
    )


def test_rank_orders_by_total_then_earliest_submission() -> None:
    quotes = [
        snapshot("late", "Late", "100.00", offset_minutes=10),
        snapshot("early", "Early", "100.00", offset_minutes=1),
        snapshot("best", "Best", "90.00", offset_minutes=20),
    ]

    ranks = rank_quotes(quotes)

    assert ranks["best"] == 1
    assert ranks["early"] == 2
    assert ranks["late"] == 3


def test_new_supplier_alone_does_not_count_as_rank_change() -> None:
    previous = {"a": 1, "b": 2}
    current = {"a": 1, "b": 2, "c": 3}

    assert ranks_changed(previous, current) is False
    assert trigger_fired(TriggerType.ANY_RANK_CHANGE.value, previous, current) is False


def test_displacing_an_existing_supplier_counts_as_rank_change() -> None:
    previous = {"a": 1, "b": 2}
    current = {"a": 2, "b": 3, "c": 1}

    assert ranks_changed(previous, current) is True
    assert trigger_fired(TriggerType.ANY_RANK_CHANGE.value, previous, current) is True


def test_l1_trigger_fires_only_when_leader_changes() -> None:
    previous = {"a": 1, "b": 2}
    same_leader = {"a": 1, "b": 3, "c": 2}
    new_leader = {"a": 2, "b": 1}

    assert trigger_fired(TriggerType.L1_RANK_CHANGE.value, previous, same_leader) is False
    assert trigger_fired(TriggerType.L1_RANK_CHANGE.value, previous, new_leader) is True
    assert trigger_fired(TriggerType.ANY_BID.value, previous, same_leader) is True


def test_first_bid_is_an_l1_change_but_not_a_rank_change() -> None:
    empty: dict[str, int] = {}
    first = {"a": 1}

    assert trigger_fired(TriggerType.L1_RANK_CHANGE.value, empty, first) is True
    assert trigger_fired(TriggerType.ANY_RANK_CHANGE.value, empty, first) is False


def test_trigger_window_is_inclusive_at_both_edges() -> None:
    close = T0 + timedelta(minutes=10)

    assert in_trigger_window(close - timedelta(minutes=10), close, 10) is True
    assert in_trigger_window(close, close, 10) is True
    assert in_trigger_window(close - timedelta(minutes=10, seconds=1), close, 10) is False


def test_extension_is_clamped_to_forced_close() -> None:
    close = T0 + timedelta(minutes=5)
    forced = T0 + timedelta(minutes=7)

    assert next_close_time(close, forced, 5) == forced
    assert next_close_time(T0, T0 + timedelta(hours=2), 5) == T0 + timedelta(minutes=5)
