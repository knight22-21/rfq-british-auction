import {
  AlertTriangle,
  ArrowLeft,
  Gavel,
  Lock,
  ShieldCheck,
  Timer,
  TrendingDown,
} from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api";
import { formatDateTime, formatMoney, triggerLabels } from "../format";
import type { BidResult, Role, RfqDetail } from "../types";
import { cardClass, secondaryButtonClass } from "../ui";
import { ActivityTimeline } from "./ActivityTimeline";
import { Countdown } from "./Countdown";
import { QuoteForm } from "./QuoteForm";
import { RankTable } from "./RankTable";
import { StatusBadge } from "./StatusBadge";

interface Notice {
  tone: "success" | "warning";
  message: string;
}

interface AuctionDetailProps {
  id: string;
  role: Role;
  carrierName: string;
  onCarrierNameChange: (value: string) => void;
  onBack: () => void;
  now: () => number;
  sync: (serverTime: string) => void;
}

export function AuctionDetail({
  id,
  role,
  carrierName,
  onCarrierNameChange,
  onBack,
  now,
  sync,
}: AuctionDetailProps) {
  const [detail, setDetail] = useState<RfqDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const result = await api.getRfq(id);
        if (!active) {
          return;
        }
        sync(result.serverTime);
        setDetail(result.data);
        setError(null);
      } catch (cause) {
        if (active) {
          setError(cause instanceof Error ? cause.message : "Could not load auction.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    const timer = window.setInterval(() => void load(), 3000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [id, sync, reloadToken]);

  function handleSubmitted(result: BidResult) {
    if (result.extension.extended) {
      setNotice({
        tone: "success",
        message: `Close time extended to ${formatDateTime(
          result.extension.newCloseTime,
        )}. ${result.extension.reason ?? ""}`,
      });
    } else if (result.extension.cappedByForcedClose) {
      setNotice({
        tone: "warning",
        message:
          "The extension trigger fired, but the auction is already at the forced close ceiling.",
      });
    } else {
      setNotice({
        tone: "success",
        message: `Quote accepted at rank L${result.rank}.`,
      });
    }
    setReloadToken((value) => value + 1);
  }

  if (loading) {
    return (
      <div className="rounded-2xl border border-white/10 bg-slate-900/40 px-6 py-24 text-center text-sm text-slate-400">
        Loading auction…
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="space-y-4">
        <button type="button" onClick={onBack} className={secondaryButtonClass}>
          <ArrowLeft size={15} />
          Back to auctions
        </button>
        <div className="flex items-center gap-2 rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">
          <AlertTriangle size={16} />
          {error ?? "Auction not found."}
        </div>
      </div>
    );
  }

  return (
    <section className="space-y-5">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-sm text-slate-400 transition hover:text-slate-100"
      >
        <ArrowLeft size={16} />
        Back to auctions
      </button>

      <div className={`${cardClass} space-y-4`}>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={detail.status} />
          <span className="font-mono text-[11px] uppercase tracking-wider text-slate-400">
            {detail.referenceId}
          </span>
          <span className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-slate-400">
            {detail.isBritishAuction ? "Auto-extension on" : "Fixed close"}
          </span>
        </div>

        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-50">
            {detail.title}
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Pickup {formatDateTime(detail.pickupDate)} · Bid window opened{" "}
            {formatDateTime(detail.bidStartTime)}
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5 text-[11px] text-slate-300">
          <span className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1">
            <TrendingDown size={12} />
            {triggerLabels[detail.extensionTrigger]}
          </span>
          <span className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1">
            <Timer size={12} />X {detail.triggerWindowMins}m
          </span>
          <span className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1">
            +Y {detail.extensionDurationMins}m
          </span>
          <span className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1">
            <Gavel size={12} />
            {detail.quoteCount} quote{detail.quoteCount === 1 ? "" : "s"}
          </span>
        </div>

        <div className="grid gap-4 border-t border-white/10 pt-4 sm:grid-cols-3">
          <div className="sm:col-span-1">
            <Countdown
              target={detail.bidCloseTime}
              now={now}
              windowMinutes={detail.triggerWindowMins}
              status={detail.status}
              variant="lg"
            />
          </div>
          <div className="rounded-xl border border-white/5 bg-slate-950/40 px-4 py-3">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">
              Lowest bid
            </p>
            <p className="mt-1 text-lg font-semibold text-emerald-300">
              {formatMoney(detail.lowestBid)}
            </p>
            <p className="truncate text-xs text-slate-400">
              {detail.lowestCarrierName ?? "No quotes yet"}
            </p>
          </div>
          <div className="rounded-xl border border-white/5 bg-slate-950/40 px-4 py-3">
            <p className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500">
              <Lock size={11} />
              Forced close
            </p>
            <p className="mt-1 text-sm font-medium text-slate-100">
              {formatDateTime(detail.forcedCloseTime)}
            </p>
            <p className="text-xs text-slate-500">Hard ceiling, never extended</p>
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.55fr_1fr]">
        <div className="space-y-5">
          <div className={cardClass}>
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-slate-100">
                Supplier leaderboard
              </h2>
              <span className="text-[11px] text-slate-500">
                Sorted by total landed cost
              </span>
            </div>
            <div className="mt-4">
              <RankTable quotes={detail.quotes} />
            </div>
          </div>

          <div className={cardClass}>
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-slate-100">Activity log</h2>
              <span className="text-[11px] text-slate-500">
                {detail.activity.length} entries
              </span>
            </div>
            <div className="mt-4">
              <ActivityTimeline entries={detail.activity} />
            </div>
          </div>
        </div>

        <div className="space-y-5">
          {notice && (
            <div
              role="status"
              className={`rounded-xl border px-4 py-3 text-sm ${
                notice.tone === "warning"
                  ? "border-amber-400/30 bg-amber-400/10 text-amber-200"
                  : "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
              }`}
            >
              {notice.message}
            </div>
          )}

          {role === "supplier" ? (
            <QuoteForm
              rfq={detail}
              carrierName={carrierName}
              onCarrierNameChange={onCarrierNameChange}
              onSubmitted={handleSubmitted}
            />
          ) : (
            <div className={cardClass}>
              <h2 className="flex items-center gap-1.5 text-sm font-semibold text-slate-100">
                <ShieldCheck size={15} className="text-emerald-300" />
                Buyer view
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">
                You are reviewing supplier quotes. Switch to the Supplier role in
                the header to place a bid, or create a new RFQ from the listing.
              </p>
            </div>
          )}

          <div className={cardClass}>
            <h2 className="flex items-center gap-1.5 text-sm font-semibold text-slate-100">
              <Timer size={15} className="text-amber-300" />
              Extension rule
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              If activity matching{" "}
              <span className="text-slate-200">
                {triggerLabels[detail.extensionTrigger].toLowerCase()}
              </span>{" "}
              happens in the final {detail.triggerWindowMins} minutes, the close
              time moves by {detail.extensionDurationMins} minutes. It can never
              pass the forced close at {formatDateTime(detail.forcedCloseTime)}.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
