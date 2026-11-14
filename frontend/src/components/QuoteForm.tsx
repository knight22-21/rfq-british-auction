import { AlertTriangle, Send } from "lucide-react";
import { useMemo, useState } from "react";

import { api } from "../api";
import { formatMoney, parseNumber } from "../format";
import type { BidResult, RfqSummary } from "../types";
import {
  cardClass,
  fieldClass,
  labelClass,
  primaryButtonClass,
} from "../ui";

function dateFromNow(days: number): string {
  return new Date(Date.now() + days * 86_400_000).toISOString().slice(0, 10);
}

export function QuoteForm({
  rfq,
  carrierName,
  onCarrierNameChange,
  onSubmitted,
}: {
  rfq: RfqSummary;
  carrierName: string;
  onCarrierNameChange: (value: string) => void;
  onSubmitted: (result: BidResult) => void;
}) {
  const [carrier, setCarrier] = useState(carrierName);
  const [freight, setFreight] = useState("");
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [transit, setTransit] = useState("14");
  const [validity, setValidity] = useState(dateFromNow(14));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const total = useMemo(
    () => parseNumber(freight) + parseNumber(origin) + parseNumber(destination),
    [freight, origin, destination],
  );

  const acceptingBids = rfq.status === "ACTIVE";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (carrier.trim().length < 2) {
      setError("Enter the carrier name submitting this quote.");
      return;
    }
    if (transit === "" || Number(transit) < 0) {
      setError("Transit time must be zero or more days.");
      return;
    }

    setBusy(true);
    try {
      const result = await api.submitQuote(rfq.id, {
        carrierName: carrier.trim(),
        freightCharges: freight || "0",
        originCharges: origin || "0",
        destinationCharges: destination || "0",
        transitTimeDays: Number(transit),
        validityDate: new Date(`${validity}T23:59:59`).toISOString(),
      });
      onCarrierNameChange(carrier.trim());
      onSubmitted(result.data);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not submit the quote.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={cardClass}>
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-100">Submit a quote</h2>
        <span className="text-[11px] text-slate-500">
          Total preview{" "}
          <span className="font-semibold text-emerald-300">
            {formatMoney(total)}
          </span>
        </span>
      </div>

      {!acceptingBids && (
        <p className="mt-3 rounded-lg border border-amber-400/20 bg-amber-400/5 px-3 py-2 text-xs text-amber-200">
          Bidding is not open right now. Quotes can be submitted while the auction
          is active.
        </p>
      )}

      <div className="mt-4 space-y-3">
        <div>
          <label className={labelClass} htmlFor="carrier">
            Carrier / supplier
          </label>
          <input
            id="carrier"
            className={fieldClass}
            value={carrier}
            onChange={(event) => setCarrier(event.target.value)}
            placeholder="Maersk"
            maxLength={100}
            required
            disabled={!acceptingBids}
          />
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className={labelClass} htmlFor="freight">
              Freight
            </label>
            <input
              id="freight"
              className={fieldClass}
              type="number"
              min={0}
              step="0.01"
              value={freight}
              onChange={(event) => setFreight(event.target.value)}
              placeholder="2150.00"
              disabled={!acceptingBids}
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="origin">
              Origin
            </label>
            <input
              id="origin"
              className={fieldClass}
              type="number"
              min={0}
              step="0.01"
              value={origin}
              onChange={(event) => setOrigin(event.target.value)}
              placeholder="340.00"
              disabled={!acceptingBids}
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="destination">
              Destination
            </label>
            <input
              id="destination"
              className={fieldClass}
              type="number"
              min={0}
              step="0.01"
              value={destination}
              onChange={(event) => setDestination(event.target.value)}
              placeholder="410.00"
              disabled={!acceptingBids}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className={labelClass} htmlFor="transit">
              Transit (days)
            </label>
            <input
              id="transit"
              className={fieldClass}
              type="number"
              min={0}
              max={365}
              value={transit}
              onChange={(event) => setTransit(event.target.value)}
              disabled={!acceptingBids}
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="validity">
              Quote valid until
            </label>
            <input
              id="validity"
              className={fieldClass}
              type="date"
              value={validity}
              onChange={(event) => setValidity(event.target.value)}
              disabled={!acceptingBids}
              required
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-xs text-rose-200">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      <button
        type="submit"
        className={`${primaryButtonClass} mt-4 w-full`}
        disabled={!acceptingBids || busy}
      >
        <Send size={15} />
        {busy ? "Submitting…" : "Submit quote"}
      </button>
    </form>
  );
}
