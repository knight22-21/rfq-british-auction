from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..domain import TERMINAL_STATUSES, AuctionStatus, EventType
from ..errors import ApiError
from ..models import Rfq
from ..schemas import RfqCreate
from ..timeutils import iso_z, utcnow
from .activity import log_event


def resolve_status_from_times(
    start: datetime, close: datetime, forced: datetime, now: datetime
) -> str:
    if now >= forced:
        return AuctionStatus.FORCE_CLOSED.value
    if now >= close:
        return AuctionStatus.CLOSED.value
    if now >= start:
        return AuctionStatus.ACTIVE.value
    return AuctionStatus.SCHEDULED.value


def resolve_status(rfq: Rfq, now: datetime) -> str:
    return resolve_status_from_times(
        rfq.bid_start_time, rfq.bid_close_time, rfq.forced_close_time, now
    )


def refresh_status(db: Session, rfq: Rfq, now: datetime | None = None) -> bool:
    now = now or utcnow()
    if rfq.status in TERMINAL_STATUSES:
        return False

    resolved = resolve_status(rfq, now)
    if resolved == rfq.status:
        return False

    previous = rfq.status
    rfq.status = resolved
    rfq.updated_at = now
    log_event(
        db,
        rfq,
        EventType.STATUS_CHANGED,
        f"Auction status moved from {previous} to {resolved}.",
        {"previousStatus": previous, "newStatus": resolved},
        at=now,
    )
    db.flush()
    return True


def create_rfq(db: Session, payload: RfqCreate, now: datetime | None = None) -> Rfq:
    now = now or utcnow()
    existing = db.scalar(select(Rfq.id).where(Rfq.reference_id == payload.reference_id))
    if existing is not None:
        raise ApiError(
            "DUPLICATE_REFERENCE",
            f"RFQ reference '{payload.reference_id}' already exists.",
            409,
        )

    rfq = Rfq(
        reference_id=payload.reference_id,
        title=payload.title.strip(),
        pickup_date=payload.pickup_date,
        bid_start_time=payload.bid_start_time,
        bid_close_time=payload.bid_close_time,
        forced_close_time=payload.forced_close_time,
        is_british_auction=payload.is_british_auction,
        trigger_window_mins=payload.trigger_window_mins,
        extension_duration_mins=payload.extension_duration_mins,
        extension_trigger=payload.extension_trigger.value,
        status=resolve_status_from_times(
            payload.bid_start_time,
            payload.bid_close_time,
            payload.forced_close_time,
            now,
        ),
        created_at=now,
        updated_at=now,
    )
    db.add(rfq)
    db.flush()
    log_event(
        db,
        rfq,
        EventType.RFQ_CREATED,
        f"RFQ {rfq.reference_id} created for {rfq.title}.",
        {
            "bidStartTime": iso_z(rfq.bid_start_time),
            "bidCloseTime": iso_z(rfq.bid_close_time),
            "forcedCloseTime": iso_z(rfq.forced_close_time),
            "triggerWindowMins": rfq.trigger_window_mins,
            "extensionDurationMins": rfq.extension_duration_mins,
            "extensionTrigger": rfq.extension_trigger,
            "isBritishAuction": rfq.is_british_auction,
        },
        at=now,
    )
    db.commit()
    db.refresh(rfq)
    return rfq


def list_rfqs(db: Session, now: datetime | None = None) -> list[Rfq]:
    now = now or utcnow()
    rfqs = list(
        db.scalars(
            select(Rfq)
            .options(selectinload(Rfq.quotes))
            .order_by(Rfq.created_at.desc())
        ).all()
    )
    changed = False
    for rfq in rfqs:
        changed = refresh_status(db, rfq, now) or changed
    if changed:
        db.commit()
    return rfqs


def get_rfq(db: Session, rfq_id: str, now: datetime | None = None) -> Rfq:
    now = now or utcnow()
    rfq = db.scalar(
        select(Rfq)
        .where(Rfq.id == rfq_id)
        .options(selectinload(Rfq.quotes), selectinload(Rfq.logs))
    )
    if rfq is None:
        raise ApiError("RFQ_NOT_FOUND", "RFQ not found.", 404)
    if refresh_status(db, rfq, now):
        db.commit()
        db.refresh(rfq)
    return rfq
