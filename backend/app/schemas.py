from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Generic, TypeVar

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    model_validator,
)
from pydantic.alias_generators import to_camel

from .domain import AuctionStatus, TriggerType
from .timeutils import coerce_utc, iso_z

UtcDateTime = Annotated[
    datetime,
    BeforeValidator(coerce_utc),
    PlainSerializer(iso_z, return_type=str, when_used="json"),
]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class RfqCreate(ApiModel):
    reference_id: Annotated[
        str,
        Field(
            min_length=3,
            max_length=50,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
        ),
    ]
    title: Annotated[str, Field(min_length=3, max_length=255)]
    pickup_date: UtcDateTime
    bid_start_time: UtcDateTime
    bid_close_time: UtcDateTime
    forced_close_time: UtcDateTime
    is_british_auction: bool = True
    trigger_window_mins: Annotated[int, Field(ge=1, le=1440)] = 10
    extension_duration_mins: Annotated[int, Field(ge=1, le=1440)] = 5
    extension_trigger: TriggerType = TriggerType.ANY_BID

    @model_validator(mode="after")
    def validate_schedule(self) -> "RfqCreate":
        if not self.bid_start_time < self.bid_close_time:
            raise ValueError("bidCloseTime must be after bidStartTime")
        if not self.bid_close_time < self.forced_close_time:
            raise ValueError("forcedCloseTime must be after bidCloseTime")
        return self


class QuoteCreate(ApiModel):
    carrier_name: Annotated[str, Field(min_length=2, max_length=100)]
    freight_charges: Annotated[
        Decimal, Field(ge=0, max_digits=12, decimal_places=2)
    ]
    origin_charges: Annotated[
        Decimal, Field(ge=0, max_digits=12, decimal_places=2)
    ]
    destination_charges: Annotated[
        Decimal, Field(ge=0, max_digits=12, decimal_places=2)
    ]
    transit_time_days: Annotated[int, Field(ge=0, le=365)]
    validity_date: UtcDateTime


class QuoteOut(ApiModel):
    id: str
    carrier_name: str
    freight_charges: Decimal
    origin_charges: Decimal
    destination_charges: Decimal
    total_amount: Decimal
    transit_time_days: int
    validity_date: UtcDateTime
    rank: int | None
    submitted_at: UtcDateTime


class ActivityOut(ApiModel):
    id: str
    event_type: str
    description: str
    metadata: dict[str, object] | None = None
    created_at: UtcDateTime


class RfqSummaryOut(ApiModel):
    id: str
    reference_id: str
    title: str
    pickup_date: UtcDateTime
    bid_start_time: UtcDateTime
    bid_close_time: UtcDateTime
    forced_close_time: UtcDateTime
    is_british_auction: bool
    trigger_window_mins: int
    extension_duration_mins: int
    extension_trigger: str
    status: AuctionStatus
    quote_count: int
    lowest_bid: Decimal | None
    lowest_carrier_name: str | None
    created_at: UtcDateTime
    updated_at: UtcDateTime


class RfqDetailOut(RfqSummaryOut):
    quotes: list[QuoteOut]
    activity: list[ActivityOut]


class BidExtensionOut(ApiModel):
    extended: bool
    trigger: str | None = None
    reason: str | None = None
    previous_close_time: UtcDateTime | None = None
    new_close_time: UtcDateTime | None = None
    capped_by_forced_close: bool = False


class BidResultOut(ApiModel):
    quote: QuoteOut
    rank: int
    rfq: RfqSummaryOut
    extension: BidExtensionOut


class ErrorBody(ApiModel):
    code: str
    message: str


DataT = TypeVar("DataT")


class Envelope(ApiModel, Generic[DataT]):
    success: bool = True
    data: DataT
    server_time: UtcDateTime
    error: ErrorBody | None = None


class ErrorEnvelope(ApiModel):
    success: bool = False
    error: ErrorBody
    server_time: UtcDateTime
