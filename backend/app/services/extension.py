from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Mapping, Sequence

from ..domain import TriggerType


@dataclass(frozen=True)
class QuoteSnapshot:
    quote_id: str
    carrier_name: str
    total_amount: Decimal
    submitted_at: datetime


def rank_quotes(quotes: Sequence[QuoteSnapshot]) -> dict[str, int]:
    """L1..Ln by price; an earlier equal-price bid keeps the better rank."""
    ordered = sorted(
        quotes,
        key=lambda quote: (quote.total_amount, quote.submitted_at, quote.quote_id),
    )
    return {quote.quote_id: index + 1 for index, quote in enumerate(ordered)}


def leader(ranks: Mapping[str, int]) -> str | None:
    for quote_id, rank in ranks.items():
        if rank == 1:
            return quote_id
    return None


def in_trigger_window(
    bid_time: datetime, close_time: datetime, window_minutes: int
) -> bool:
    return close_time - timedelta(minutes=window_minutes) <= bid_time <= close_time


def ranks_changed(
    previous: Mapping[str, int], current: Mapping[str, int]
) -> bool:
    """A new supplier entering the field is not, by itself, a rank change."""
    return any(current.get(quote_id) != rank for quote_id, rank in previous.items())


def trigger_fired(
    trigger: str,
    previous: Mapping[str, int],
    current: Mapping[str, int],
) -> bool:
    if trigger == TriggerType.ANY_BID.value:
        return True
    if trigger == TriggerType.ANY_RANK_CHANGE.value:
        return ranks_changed(previous, current)
    if trigger == TriggerType.L1_RANK_CHANGE.value:
        return leader(previous) != leader(current)
    return False


def next_close_time(
    close_time: datetime, forced_close_time: datetime, extension_minutes: int
) -> datetime:
    return min(
        close_time + timedelta(minutes=extension_minutes), forced_close_time
    )


def trigger_reason(trigger: str, window_minutes: int) -> str:
    if trigger == TriggerType.ANY_RANK_CHANGE.value:
        return (
            "Supplier rankings changed inside the "
            f"{window_minutes}-minute trigger window."
        )
    if trigger == TriggerType.L1_RANK_CHANGE.value:
        return (
            "The lowest bidder (L1) changed inside the "
            f"{window_minutes}-minute trigger window."
        )
    return f"A bid was received inside the {window_minutes}-minute trigger window."
