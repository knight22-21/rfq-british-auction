from __future__ import annotations

from enum import Enum


class TriggerType(str, Enum):
    ANY_BID = "ANY_BID"
    ANY_RANK_CHANGE = "ANY_RANK_CHANGE"
    L1_RANK_CHANGE = "L1_RANK_CHANGE"


class AuctionStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    FORCE_CLOSED = "FORCE_CLOSED"


class EventType(str, Enum):
    RFQ_CREATED = "RFQ_CREATED"
    BID_SUBMITTED = "BID_SUBMITTED"
    RANK_CHANGED = "RANK_CHANGED"
    AUCTION_EXTENDED = "AUCTION_EXTENDED"
    EXTENSION_BLOCKED = "EXTENSION_BLOCKED"
    STATUS_CHANGED = "STATUS_CHANGED"


TERMINAL_STATUSES = {AuctionStatus.CLOSED.value, AuctionStatus.FORCE_CLOSED.value}
