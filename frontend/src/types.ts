export type AuctionStatus = "SCHEDULED" | "ACTIVE" | "CLOSED" | "FORCE_CLOSED";

export type TriggerType = "ANY_BID" | "ANY_RANK_CHANGE" | "L1_RANK_CHANGE";

export type Role = "buyer" | "supplier";

export interface Activity {
  id: string;
  eventType: string;
  description: string;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface Quote {
  id: string;
  carrierName: string;
  freightCharges: string;
  originCharges: string;
  destinationCharges: string;
  totalAmount: string;
  transitTimeDays: number;
  validityDate: string;
  rank: number | null;
  submittedAt: string;
}

export interface RfqSummary {
  id: string;
  referenceId: string;
  title: string;
  pickupDate: string;
  bidStartTime: string;
  bidCloseTime: string;
  forcedCloseTime: string;
  isBritishAuction: boolean;
  triggerWindowMins: number;
  extensionDurationMins: number;
  extensionTrigger: TriggerType;
  status: AuctionStatus;
  quoteCount: number;
  lowestBid: string | null;
  lowestCarrierName: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface RfqDetail extends RfqSummary {
  quotes: Quote[];
  activity: Activity[];
}

export interface BidExtension {
  extended: boolean;
  trigger: TriggerType | null;
  reason: string | null;
  previousCloseTime: string | null;
  newCloseTime: string | null;
  cappedByForcedClose: boolean;
}

export interface BidResult {
  quote: Quote;
  rank: number;
  rfq: RfqSummary;
  extension: BidExtension;
}

export interface RfqCreateInput {
  referenceId: string;
  title: string;
  pickupDate: string;
  bidStartTime: string;
  bidCloseTime: string;
  forcedCloseTime: string;
  isBritishAuction: boolean;
  triggerWindowMins: number;
  extensionDurationMins: number;
  extensionTrigger: TriggerType;
}

export interface QuoteCreateInput {
  carrierName: string;
  freightCharges: string;
  originCharges: string;
  destinationCharges: string;
  transitTimeDays: number;
  validityDate: string;
}
