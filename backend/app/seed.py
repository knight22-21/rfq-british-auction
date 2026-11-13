from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .domain import TriggerType
from .models import Rfq
from .schemas import QuoteCreate, RfqCreate
from .services import bid_service, rfq_service
from .timeutils import utcnow


def _quote(
    carrier: str,
    freight: str,
    origin: str,
    destination: str,
    transit: int,
    validity: datetime,
) -> QuoteCreate:
    return QuoteCreate(
        carrier_name=carrier,
        freight_charges=Decimal(freight),
        origin_charges=Decimal(origin),
        destination_charges=Decimal(destination),
        transit_time_days=transit,
        validity_date=validity,
    )


def seed_if_empty(db: Session) -> bool:
    if db.scalar(select(func.count()).select_from(Rfq)):
        return False

    now = utcnow()

    rfq_service.create_rfq(
        db,
        RfqCreate(
            reference_id="RFQ-2026-001",
            title="Shanghai to Rotterdam | 40ft HC",
            pickup_date=now + timedelta(days=12),
            bid_start_time=now - timedelta(hours=2),
            bid_close_time=now + timedelta(minutes=18),
            forced_close_time=now + timedelta(hours=1),
            trigger_window_mins=10,
            extension_duration_mins=5,
            extension_trigger=TriggerType.ANY_RANK_CHANGE,
        ),
        now=now - timedelta(hours=2),
    )
    first = rfq_service.get_rfq(
        db,
        db.scalar(
            select(Rfq.id).where(Rfq.reference_id == "RFQ-2026-001")
        ),
        now=now,
    )
    for minutes_ago, quote in [
        (45, _quote("Maersk", "2150.00", "340.00", "410.00", 31, now + timedelta(days=30))),
        (30, _quote("MSC", "2080.00", "355.00", "425.00", 33, now + timedelta(days=30))),
        (12, _quote("Hapag-Lloyd", "2040.00", "365.00", "430.00", 32, now + timedelta(days=30))),
    ]:
        bid_service.submit_quote(db, first.id, quote, now=now - timedelta(minutes=minutes_ago))

    rfq_service.create_rfq(
        db,
        RfqCreate(
            reference_id="RFQ-2026-002",
            title="Nhava Sheva to Hamburg | 20ft GP",
            pickup_date=now + timedelta(days=9),
            bid_start_time=now - timedelta(hours=2),
            bid_close_time=now + timedelta(minutes=2),
            forced_close_time=now + timedelta(minutes=30),
            trigger_window_mins=10,
            extension_duration_mins=5,
            extension_trigger=TriggerType.ANY_BID,
        ),
        now=now - timedelta(hours=2),
    )
    second = rfq_service.get_rfq(
        db,
        db.scalar(
            select(Rfq.id).where(Rfq.reference_id == "RFQ-2026-002")
        ),
        now=now,
    )
    for minutes_ago, quote in [
        (
            5,
            _quote(
                "CMA CGM",
                "1780.00",
                "290.00",
                "365.00",
                26,
                now + timedelta(days=21),
            ),
        ),
        (
            3,
            _quote(
                "COSCO",
                "1745.00",
                "305.00",
                "350.00",
                28,
                now + timedelta(days=21),
            ),
        ),
    ]:
        bid_service.submit_quote(db, second.id, quote, now=now - timedelta(minutes=minutes_ago))

    rfq_service.create_rfq(
        db,
        RfqCreate(
            reference_id="RFQ-2026-003",
            title="Chennai to Singapore | LCL",
            pickup_date=now + timedelta(days=20),
            bid_start_time=now + timedelta(hours=2),
            bid_close_time=now + timedelta(hours=3),
            forced_close_time=now + timedelta(hours=4),
            trigger_window_mins=15,
            extension_duration_mins=10,
            extension_trigger=TriggerType.L1_RANK_CHANGE,
        ),
        now=now,
    )

    rfq_service.create_rfq(
        db,
        RfqCreate(
            reference_id="RFQ-2026-004",
            title="Mundra to Jebel Ali | 40ft DV",
            pickup_date=now + timedelta(days=6),
            bid_start_time=now - timedelta(hours=3),
            bid_close_time=now + timedelta(minutes=20),
            forced_close_time=now + timedelta(hours=2),
            trigger_window_mins=10,
            extension_duration_mins=5,
            extension_trigger=TriggerType.ANY_BID,
        ),
        now=now - timedelta(hours=3),
    )
    closed = rfq_service.get_rfq(
        db,
        db.scalar(
            select(Rfq.id).where(Rfq.reference_id == "RFQ-2026-004")
        ),
        now=now,
    )
    for minutes_ago, quote in [
        (150, _quote("MSC", "1120.00", "210.00", "265.00", 4, now + timedelta(days=14))),
        (120, _quote("Maersk", "1095.00", "225.00", "250.00", 5, now + timedelta(days=14))),
        (75, _quote("ONE", "1075.00", "220.00", "260.00", 6, now + timedelta(days=14))),
    ]:
        bid_service.submit_quote(db, closed.id, quote, now=now - timedelta(minutes=minutes_ago))

    closed.bid_close_time = now - timedelta(hours=1)
    closed.status = "ACTIVE"
    db.add(closed)
    db.commit()

    return True
