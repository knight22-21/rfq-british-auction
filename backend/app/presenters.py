from __future__ import annotations

from .models import ActivityLog, Quote, Rfq
from .schemas import ActivityOut, QuoteOut, RfqDetailOut, RfqSummaryOut

ACTIVITY_PAGE_SIZE = 100


def ordered_quotes(rfq: Rfq) -> list[Quote]:
    return sorted(
        rfq.quotes,
        key=lambda quote: (
            quote.rank if quote.rank is not None else 10**9,
            quote.total_amount,
            quote.submitted_at,
            quote.id,
        ),
    )


def quote_out(quote: Quote) -> QuoteOut:
    return QuoteOut.model_validate(quote)


def activity_out(entry: ActivityLog) -> ActivityOut:
    return ActivityOut(
        id=entry.id,
        event_type=entry.event_type,
        description=entry.description,
        metadata=entry.metadata_,
        created_at=entry.created_at,
    )


def rfq_summary(rfq: Rfq) -> RfqSummaryOut:
    lowest = min(
        rfq.quotes,
        key=lambda quote: (quote.total_amount, quote.submitted_at, quote.id),
        default=None,
    )
    return RfqSummaryOut(
        id=rfq.id,
        reference_id=rfq.reference_id,
        title=rfq.title,
        pickup_date=rfq.pickup_date,
        bid_start_time=rfq.bid_start_time,
        bid_close_time=rfq.bid_close_time,
        forced_close_time=rfq.forced_close_time,
        is_british_auction=rfq.is_british_auction,
        trigger_window_mins=rfq.trigger_window_mins,
        extension_duration_mins=rfq.extension_duration_mins,
        extension_trigger=rfq.extension_trigger,
        status=rfq.status,
        quote_count=len(rfq.quotes),
        lowest_bid=lowest.total_amount if lowest else None,
        lowest_carrier_name=lowest.carrier_name if lowest else None,
        created_at=rfq.created_at,
        updated_at=rfq.updated_at,
    )


def rfq_detail(rfq: Rfq) -> RfqDetailOut:
    summary = rfq_summary(rfq)
    return RfqDetailOut(
        **summary.model_dump(),
        quotes=[quote_out(quote) for quote in ordered_quotes(rfq)],
        activity=[activity_out(entry) for entry in rfq.logs[:ACTIVITY_PAGE_SIZE]],
    )
