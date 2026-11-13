from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .db import get_db
from .presenters import activity_out, quote_out, rfq_detail, rfq_summary
from .schemas import (
    ActivityOut,
    BidExtensionOut,
    BidResultOut,
    Envelope,
    QuoteCreate,
    RfqCreate,
    RfqDetailOut,
    RfqSummaryOut,
)
from .services import bid_service, rfq_service
from .timeutils import utcnow

router = APIRouter(prefix="/api")


@router.get("/health", response_model=Envelope[dict[str, str]])
def health() -> Envelope[dict[str, str]]:
    return Envelope[dict[str, str]](data={"status": "ok"}, server_time=utcnow())


@router.post(
    "/rfqs", response_model=Envelope[RfqSummaryOut], status_code=201
)
def create_rfq(
    payload: RfqCreate, db: Session = Depends(get_db)
) -> Envelope[RfqSummaryOut]:
    rfq = rfq_service.create_rfq(db, payload)
    return Envelope[RfqSummaryOut](data=rfq_summary(rfq), server_time=utcnow())


@router.get("/rfqs", response_model=Envelope[list[RfqSummaryOut]])
def list_rfqs(db: Session = Depends(get_db)) -> Envelope[list[RfqSummaryOut]]:
    rfqs = rfq_service.list_rfqs(db)
    return Envelope[list[RfqSummaryOut]](
        data=[rfq_summary(rfq) for rfq in rfqs], server_time=utcnow()
    )


@router.get("/rfqs/{rfq_id}", response_model=Envelope[RfqDetailOut])
def get_rfq(rfq_id: str, db: Session = Depends(get_db)) -> Envelope[RfqDetailOut]:
    rfq = rfq_service.get_rfq(db, rfq_id)
    return Envelope[RfqDetailOut](data=rfq_detail(rfq), server_time=utcnow())


@router.get("/rfqs/{rfq_id}/activity", response_model=Envelope[list[ActivityOut]])
def get_activity(
    rfq_id: str, db: Session = Depends(get_db)
) -> Envelope[list[ActivityOut]]:
    rfq = rfq_service.get_rfq(db, rfq_id)
    return Envelope[list[ActivityOut]](
        data=[activity_out(entry) for entry in rfq.logs], server_time=utcnow()
    )


@router.post(
    "/rfqs/{rfq_id}/quotes", response_model=Envelope[BidResultOut], status_code=201
)
def submit_quote(
    rfq_id: str, payload: QuoteCreate, db: Session = Depends(get_db)
) -> Envelope[BidResultOut]:
    outcome = bid_service.submit_quote(db, rfq_id, payload)
    return Envelope[BidResultOut](
        data=BidResultOut(
            quote=quote_out(outcome.quote),
            rank=outcome.rank,
            rfq=rfq_summary(outcome.rfq),
            extension=BidExtensionOut.model_validate(outcome.extension),
        ),
        server_time=utcnow(),
    )
