from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .domain import AuctionStatus, EventType, TriggerType
from .timeutils import utcnow


def new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Rfq(Base):
    __tablename__ = "rfqs"
    __table_args__ = (
        # Strictly greater at creation; equality is reachable when an extension
        # is clamped against the forced close ceiling.
        CheckConstraint(
            "forced_close_time >= bid_close_time", name="ck_rfq_forced_after_close"
        ),
        CheckConstraint(
            "bid_close_time > bid_start_time", name="ck_rfq_close_after_start"
        ),
        CheckConstraint(
            "trigger_window_mins > 0", name="ck_rfq_positive_trigger_window"
        ),
        CheckConstraint(
            "extension_duration_mins > 0", name="ck_rfq_positive_extension"
        ),
        Index("ix_rfqs_status_close", "status", "bid_close_time"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reference_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    pickup_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    bid_start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    bid_close_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    forced_close_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_british_auction: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    trigger_window_mins: Mapped[int] = mapped_column(Integer, nullable=False)
    extension_duration_mins: Mapped[int] = mapped_column(Integer, nullable=False)
    extension_trigger: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TriggerType.ANY_BID.value
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AuctionStatus.SCHEDULED.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    quotes: Mapped[list["Quote"]] = relationship(
        back_populates="rfq",
        cascade="all, delete-orphan",
        order_by="Quote.submitted_at",
    )
    logs: Mapped[list["ActivityLog"]] = relationship(
        back_populates="rfq",
        cascade="all, delete-orphan",
        order_by="ActivityLog.created_at.desc()",
    )


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (
        CheckConstraint("freight_charges >= 0", name="ck_quote_freight_non_negative"),
        CheckConstraint("origin_charges >= 0", name="ck_quote_origin_non_negative"),
        CheckConstraint(
            "destination_charges >= 0", name="ck_quote_destination_non_negative"
        ),
        CheckConstraint("transit_time_days >= 0", name="ck_quote_transit_non_negative"),
        Index("ix_quotes_rfq_total", "rfq_id", "total_amount", "submitted_at"),
        Index("ix_quotes_rfq_rank", "rfq_id", "rank"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rfq_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False
    )
    carrier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    freight_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    origin_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    destination_charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    transit_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    validity_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow
    )

    rfq: Mapped[Rfq] = relationship(back_populates="quotes")


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_logs_rfq_created", "rfq_id", "created_at"),
        Index("ix_activity_logs_event_type", "event_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rfq_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EventType.BID_SUBMITTED.value
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, object] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow
    )

    rfq: Mapped[Rfq] = relationship(back_populates="logs")
