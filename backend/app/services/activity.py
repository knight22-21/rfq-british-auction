from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..domain import EventType
from ..models import ActivityLog, Rfq
from ..timeutils import utcnow


def log_event(
    db: Session,
    rfq: Rfq,
    event_type: EventType,
    description: str,
    metadata: dict[str, object] | None = None,
    at: datetime | None = None,
) -> ActivityLog:
    entry = ActivityLog(
        rfq_id=rfq.id,
        event_type=event_type.value,
        description=description,
        metadata_=metadata,
        created_at=at or utcnow(),
    )
    db.add(entry)
    return entry
