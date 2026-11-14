import { statusLabels } from "../format";
import type { AuctionStatus } from "../types";

const styles: Record<AuctionStatus, string> = {
  ACTIVE: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  SCHEDULED: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  CLOSED: "border-slate-400/30 bg-slate-400/10 text-slate-300",
  FORCE_CLOSED: "border-rose-400/30 bg-rose-400/10 text-rose-300",
};

const dots: Record<AuctionStatus, string> = {
  ACTIVE: "bg-emerald-400",
  SCHEDULED: "bg-sky-400",
  CLOSED: "bg-slate-400",
  FORCE_CLOSED: "bg-rose-400",
};

export function StatusBadge({ status }: { status: AuctionStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide ${styles[status]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dots[status]}`} />
      {statusLabels[status]}
    </span>
  );
}
