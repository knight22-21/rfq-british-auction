from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain import AuctionStatus, EventType
from ..errors import ApiError
from ..models import Quote, Rfq
from ..schemas import QuoteCreate
from ..timeutils import iso_z, utcnow
from .activity import log_event
from .extension import (
    QuoteSnapshot,
    in_trigger_window,
    next_close_time,
    rank_quotes,
    ranks_changed,
    trigger_fired,
    trigger_reason,
)
from .rfq_service import refresh_status


@dataclass(frozen=True)
class BidOutcome:
    rfq: Rfq
    quote: Quote
    rank: int
    extension: dict[str, object]


def _snapshot(quote: Quote) -> QuoteSnapshot:
    return QuoteSnapshot(
        quote_id=quote.id,
        carrier_name=quote.carrier_name,
        total_amount=Decimal(quote.total_amount),
        submitted_at=quote.submitted_at,
    )


def _format_time(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")


def _no_extension() -> dict[str, object]:
    return {
        "extended": False,
        "trigger": None,
        "reason": None,
        "previous_close_time": None,
        "new_close_time": None,
        "capped_by_forced_close": False,
    }


def _close_if_not_active(db: Session, rfq: Rfq, now: datetime) -> None:
    if refresh_status(db, rfq, now):
        db.commit()

    rejection = {
        AuctionStatus.SCHEDULED.value: (
            "BIDDING_NOT_OPEN",
            "Bidding has not started for this RFQ yet.",
        ),
        AuctionStatus.CLOSED.value: (
            "AUCTION_CLOSED",
            "Bidding is closed for this RFQ.",
        ),
        AuctionStatus.FORCE_CLOSED.value: (
            "AUCTION_FORCE_CLOSED",
            "The forced close time has passed; no further bids are accepted.",
        ),
    }
    if rfq.status != AuctionStatus.ACTIVE.value:
        code, message = rejection.get(
            rfq.status, ("AUCTION_NOT_ACTIVE", "This auction is not accepting bids.")
        )
        raise ApiError(code, message, 409)


def _apply_extension(
    db: Session,
    rfq: Rfq,
    quote: Quote,
    previous_ranks: dict[str, int],
    current_ranks: dict[str, int],
    now: datetime,
    next_tick,
) -> dict[str, object]:
    if not rfq.is_british_auction:
        return _no_extension()
    if not in_trigger_window(now, rfq.bid_close_time, rfq.trigger_window_mins):
        return _no_extension()
    if not trigger_fired(rfq.extension_trigger, previous_ranks, current_ranks):
        return _no_extension()

    reason = trigger_reason(rfq.extension_trigger, rfq.trigger_window_mins)
    previous_close = rfq.bid_close_time
    proposed_close = next_close_time(
        previous_close, rfq.forced_close_time, rfq.extension_duration_mins
    )

    if proposed_close <= previous_close:
        log_event(
            db,
            rfq,
            EventType.EXTENSION_BLOCKED,
            (
                f"{quote.carrier_name} bid inside the trigger window, but the close "
                f"time is already at the forced ceiling ({_format_time(previous_close)})."
            ),
            {
                "trigger": rfq.extension_trigger,
                "reason": reason,
                "closeTime": iso_z(previous_close),
                "forcedCloseTime": iso_z(rfq.forced_close_time),
            },
            at=next_tick(),
        )
        result = _no_extension()
        result.update(
            {
                "trigger": rfq.extension_trigger,
                "reason": reason,
                "previous_close_time": previous_close,
                "new_close_time": previous_close,
                "capped_by_forced_close": True,
            }
        )
        return result

    rfq.bid_close_time = proposed_close
    rfq.updated_at = now
    added_minutes = int((proposed_close - previous_close).total_seconds() // 60)
    capped = proposed_close == rfq.forced_close_time

    log_event(
        db,
        rfq,
        EventType.AUCTION_EXTENDED,
        (
            f"Close time extended from {_format_time(previous_close)} to "
            f"{_format_time(proposed_close)}. {reason}"
        ),
        {
            "previousCloseTime": iso_z(previous_close),
            "newCloseTime": iso_z(proposed_close),
            "extensionMinutes": added_minutes,
            "configuredExtensionMins": rfq.extension_duration_mins,
            "trigger": rfq.extension_trigger,
            "reason": reason,
            "triggerWindowMins": rfq.trigger_window_mins,
            "cappedByForcedClose": capped,
            "carrierName": quote.carrier_name,
        },
        at=next_tick(),
    )

    return {
        "extended": True,
        "trigger": rfq.extension_trigger,
        "reason": reason,
        "previous_close_time": previous_close,
        "new_close_time": proposed_close,
        "capped_by_forced_close": capped,
    }


def submit_quote(
    db: Session,
    rfq_id: str,
    payload: QuoteCreate,
    now: datetime | None = None,
) -> BidOutcome:
    rfq = db.scalar(select(Rfq).where(Rfq.id == rfq_id).with_for_update())
    if rfq is None:
        raise ApiError("RFQ_NOT_FOUND", "RFQ not found.", 404)

    # Timestamp once the write lock is held so timestamps and the activity feed
    # reflect the order in which concurrent bids are actually serialised.
    now = now or utcnow()
    _close_if_not_active(db, rfq, now)

    if payload.validity_date <= now:
        raise ApiError(
            "INVALID_QUOTE_VALIDITY",
            "Quote validity must be after the submission time.",
            422,
        )

    previous_quotes = list(
        db.scalars(select(Quote).where(Quote.rfq_id == rfq.id)).all()
    )
    previous_snapshots = [_snapshot(quote) for quote in previous_quotes]
    previous_ranks = rank_quotes(previous_snapshots)

    total = (
        payload.freight_charges
        + payload.origin_charges
        + payload.destination_charges
    ).quantize(Decimal("0.01"))

    quote = Quote(
        rfq_id=rfq.id,
        carrier_name=payload.carrier_name.strip(),
        freight_charges=payload.freight_charges,
        origin_charges=payload.origin_charges,
        destination_charges=payload.destination_charges,
        total_amount=total,
        transit_time_days=payload.transit_time_days,
        validity_date=payload.validity_date,
        submitted_at=now,
    )
    db.add(quote)
    db.flush()

    snapshots = previous_snapshots + [_snapshot(quote)]
    current_ranks = rank_quotes(snapshots)
    for existing in previous_quotes:
        existing.rank = current_ranks[existing.id]
    quote.rank = current_ranks[quote.id]

    tick_offset = 0

    def next_tick() -> datetime:
        nonlocal tick_offset
        tick_offset += 1
        return now + timedelta(microseconds=tick_offset)

    log_event(
        db,
        rfq,
        EventType.BID_SUBMITTED,
        (
            f"{quote.carrier_name} submitted a quote of {total:.2f} "
            f"(L{quote.rank})."
        ),
        {
            "quoteId": quote.id,
            "carrierName": quote.carrier_name,
            "totalAmount": f"{total:.2f}",
            "freightCharges": f"{payload.freight_charges:.2f}",
            "originCharges": f"{payload.origin_charges:.2f}",
            "destinationCharges": f"{payload.destination_charges:.2f}",
            "rank": quote.rank,
            "submittedAt": iso_z(now),
        },
        at=now,
    )

    if ranks_changed(previous_ranks, current_ranks):
        names = {snapshot.quote_id: snapshot.carrier_name for snapshot in snapshots}
        changes = [
            {
                "carrierName": names[quote_id],
                "fromRank": previous_rank,
                "toRank": current_ranks[quote_id],
            }
            for quote_id, previous_rank in previous_ranks.items()
            if current_ranks.get(quote_id) != previous_rank
        ]
        summary = ", ".join(
            f"{change['carrierName']} L{change['fromRank']} to L{change['toRank']}"
            for change in changes
        )
        log_event(
            db,
            rfq,
            EventType.RANK_CHANGED,
            f"Supplier rankings changed: {summary}.",
            {"changes": changes},
            at=next_tick(),
        )

    extension = _apply_extension(
        db, rfq, quote, previous_ranks, current_ranks, now, next_tick
    )
    rfq.updated_at = now

    db.commit()
    db.refresh(rfq)
    db.refresh(quote)
    return BidOutcome(rfq=rfq, quote=quote, rank=int(quote.rank or 0), extension=extension)
