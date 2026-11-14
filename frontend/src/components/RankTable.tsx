import { Inbox, Trophy } from "lucide-react";

import { formatDateTime, formatMoney } from "../format";
import type { Quote } from "../types";

export function RankTable({ quotes }: { quotes: Quote[] }) {
  if (quotes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/10 px-6 py-12 text-center">
        <Inbox size={26} className="text-slate-500" />
        <p className="mt-3 text-sm text-slate-300">No quotes submitted yet.</p>
        <p className="mt-1 text-xs text-slate-500">
          The first valid quote becomes L1.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-white/10 text-[10px] uppercase tracking-wider text-slate-500">
            <th className="py-2 pr-3 font-medium">Rank</th>
            <th className="py-2 pr-3 font-medium">Supplier</th>
            <th className="py-2 pr-3 text-right font-medium">Total</th>
            <th className="py-2 pr-3 text-right font-medium">Freight</th>
            <th className="py-2 pr-3 text-right font-medium">Origin</th>
            <th className="py-2 pr-3 text-right font-medium">Destination</th>
            <th className="py-2 pr-3 text-right font-medium">Transit</th>
            <th className="py-2 pr-3 font-medium">Valid until</th>
            <th className="py-2 text-right font-medium">Submitted</th>
          </tr>
        </thead>
        <tbody>
          {quotes.map((quote) => (
            <tr
              key={quote.id}
              className={`border-b border-white/5 last:border-0 ${
                quote.rank === 1 ? "bg-emerald-400/5" : ""
              }`}
            >
              <td className="py-3 pr-3">
                <span
                  className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-semibold ${
                    quote.rank === 1
                      ? "bg-emerald-400/15 text-emerald-300"
                      : "bg-white/5 text-slate-300"
                  }`}
                >
                  {quote.rank === 1 && <Trophy size={12} />}
                  L{quote.rank ?? "—"}
                </span>
              </td>
              <td className="py-3 pr-3 font-medium text-slate-100">
                {quote.carrierName}
              </td>
              <td className="py-3 pr-3 text-right font-semibold text-slate-50">
                {formatMoney(quote.totalAmount)}
              </td>
              <td className="py-3 pr-3 text-right text-slate-400">
                {formatMoney(quote.freightCharges)}
              </td>
              <td className="py-3 pr-3 text-right text-slate-400">
                {formatMoney(quote.originCharges)}
              </td>
              <td className="py-3 pr-3 text-right text-slate-400">
                {formatMoney(quote.destinationCharges)}
              </td>
              <td className="py-3 pr-3 text-right text-slate-400">
                {quote.transitTimeDays}d
              </td>
              <td className="py-3 pr-3 text-slate-400">
                {formatDateTime(quote.validityDate)}
              </td>
              <td className="py-3 text-right text-slate-400">
                {formatDateTime(quote.submittedAt)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
