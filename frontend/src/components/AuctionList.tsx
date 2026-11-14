import { AlertTriangle, Gavel, Plus, RefreshCw, Timer, TrendingDown } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api";
import { formatDateTime, formatMoney, triggerLabels } from "../format";
import type { AuctionStatus, RfqSummary, Role } from "../types";
import { Countdown } from "./Countdown";
import { StatusBadge } from "./StatusBadge";

type Filter = "ALL" | "ACTIVE" | "SCHEDULED" | "CLOSED";

const filters: { value: Filter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "ACTIVE", label: "Active" },
  { value: "SCHEDULED", label: "Scheduled" },
  { value: "CLOSED", label: "Closed" },
];

function matchesFilter(status: AuctionStatus, filter: Filter): boolean {
  if (filter === "ALL") {
    return true;
  }
  if (filter === "CLOSED") {
    return status === "CLOSED" || status === "FORCE_CLOSED";
  }
  return status === filter;
}

interface AuctionListProps {
  role: Role;
  now: () => number;
  sync: (serverTime: string) => void;
  onOpen: (id: string) => void;
  onCreate: () => void;
}

export function AuctionList({ role, now, sync, onOpen, onCreate }: AuctionListProps) {
  const [rfqs, setRfqs] = useState<RfqSummary[]>([]);
  const [filter, setFilter] = useState<Filter>("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const result = await api.listRfqs();
        if (!active) {
          return;
        }
        sync(result.serverTime);
        setRfqs(result.data);
        setError(null);
      } catch (cause) {
        if (active) {
          setError(cause instanceof Error ? cause.message : "Could not load auctions.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    const timer = window.setInterval(() => void load(), 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [sync, reloadToken]);

  const visible = useMemo(
    () => rfqs.filter((rfq) => matchesFilter(rfq.status, filter)),
    [rfqs, filter],
  );

  const activeCount = rfqs.filter((rfq) => rfq.status === "ACTIVE").length;

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
            Auction listing
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {rfqs.length} RFQs · {activeCount} live now
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setReloadToken((value) => value + 1)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:border-sky-400/40 hover:text-sky-200"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          {role === "buyer" && (
            <button
              type="button"
              onClick={onCreate}
              className="inline-flex items-center gap-1.5 rounded-lg bg-sky-500 px-3 py-2 text-xs font-semibold text-slate-950 transition hover:bg-sky-400"
            >
              <Plus size={14} />
              New RFQ
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {filters.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setFilter(option.value)}
            className={`rounded-full border px-3 py-1.5 text-xs transition ${
              filter === option.value
                ? "border-sky-400/40 bg-sky-400/10 text-sky-200"
                : "border-white/10 text-slate-400 hover:text-slate-200"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((key) => (
            <div
              key={key}
              className="h-56 animate-pulse rounded-2xl border border-white/10 bg-slate-900/40"
            />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 bg-slate-900/30 px-6 py-16 text-center">
          <Gavel className="mx-auto text-slate-500" size={28} />
          <p className="mt-3 text-sm text-slate-300">No auctions in this view.</p>
          {role === "buyer" && (
            <button
              type="button"
              onClick={onCreate}
              className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-sky-500 px-3 py-2 text-xs font-semibold text-slate-950 transition hover:bg-sky-400"
            >
              <Plus size={14} />
              Create the first RFQ
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {visible.map((rfq) => (
            <button
              key={rfq.id}
              type="button"
              onClick={() => onOpen(rfq.id)}
              className="group flex flex-col rounded-2xl border border-white/10 bg-slate-900/60 p-5 text-left transition hover:-translate-y-0.5 hover:border-sky-400/40 hover:bg-slate-900"
            >
              <div className="flex items-start justify-between gap-3">
                <span className="font-mono text-[11px] uppercase tracking-wider text-slate-400">
                  {rfq.referenceId}
                </span>
                <StatusBadge status={rfq.status} />
              </div>

              <h2 className="mt-2 line-clamp-2 text-base font-semibold text-slate-100 group-hover:text-white">
                {rfq.title}
              </h2>

              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-white/5 bg-slate-950/40 px-3 py-2.5">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500">
                    Lowest bid
                  </p>
                  <p className="mt-1 text-sm font-semibold text-emerald-300">
                    {formatMoney(rfq.lowestBid)}
                  </p>
                  <p className="truncate text-[11px] text-slate-500">
                    {rfq.lowestCarrierName ?? "No quotes yet"}
                  </p>
                </div>
                <div className="rounded-xl border border-white/5 bg-slate-950/40 px-3 py-2.5">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500">
                    Time left
                  </p>
                  <div className="mt-1">
                    <Countdown
                      target={rfq.bidCloseTime}
                      now={now}
                      windowMinutes={rfq.triggerWindowMins}
                      status={rfq.status}
                    />
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {rfq.quoteCount} quote{rfq.quoteCount === 1 ? "" : "s"}
                  </p>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-1.5 text-[11px] text-slate-400">
                <span className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1">
                  <TrendingDown size={12} />
                  {triggerLabels[rfq.extensionTrigger]}
                </span>
                <span className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1">
                  <Timer size={12} />X {rfq.triggerWindowMins}m · +Y{" "}
                  {rfq.extensionDurationMins}m
                </span>
              </div>

              <p className="mt-auto pt-4 text-[11px] text-slate-500">
                Forced close {formatDateTime(rfq.forcedCloseTime)}
              </p>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
