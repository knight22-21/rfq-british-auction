import {
  Activity,
  AlertTriangle,
  FilePlus2,
  Gavel,
  RefreshCw,
  Timer,
  TrendingDown,
} from "lucide-react";
import type { ComponentType } from "react";

import { formatDateTime } from "../format";
import type { Activity as ActivityEntry } from "../types";

const eventStyles: Record<
  string,
  { icon: ComponentType<{ size?: number; className?: string }>; tone: string }
> = {
  RFQ_CREATED: { icon: FilePlus2, tone: "text-sky-300" },
  BID_SUBMITTED: { icon: Gavel, tone: "text-slate-200" },
  RANK_CHANGED: { icon: TrendingDown, tone: "text-emerald-300" },
  AUCTION_EXTENDED: { icon: Timer, tone: "text-amber-300" },
  EXTENSION_BLOCKED: { icon: AlertTriangle, tone: "text-rose-300" },
  STATUS_CHANGED: { icon: RefreshCw, tone: "text-slate-400" },
};

function metaString(entry: ActivityEntry, key: string): string | null {
  const value = entry.metadata?.[key];
  return typeof value === "string" ? value : null;
}

function metaBoolean(entry: ActivityEntry, key: string): boolean {
  return entry.metadata?.[key] === true;
}

function extensionDetail(entry: ActivityEntry) {
  const previous = metaString(entry, "previousCloseTime");
  const next = metaString(entry, "newCloseTime");
  if (!previous || !next) {
    return null;
  }
  return (
    <p className="mt-1.5 text-[11px] text-amber-200/80">
      {formatDateTime(previous)} → {formatDateTime(next)}
      {metaBoolean(entry, "cappedByForcedClose") && " · clamped at forced close"}
    </p>
  );
}

export function ActivityTimeline({ entries }: { entries: ActivityEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-sm text-slate-400">No activity recorded yet.</p>;
  }

  return (
    <ol className="relative space-y-4 border-l border-white/10 pl-5">
      {entries.map((entry) => {
        const style = eventStyles[entry.eventType] ?? {
          icon: Activity,
          tone: "text-slate-400",
        };
        const Icon = style.icon;
        return (
          <li key={entry.id} className="relative">
            <span className="absolute -left-[27px] top-0.5 grid h-5 w-5 place-items-center rounded-full border border-white/10 bg-slate-950">
              <Icon size={11} className={style.tone} />
            </span>
            <p className="text-sm leading-snug text-slate-200">
              {entry.description}
            </p>
            {extensionDetail(entry)}
            <p className="mt-1 text-[10px] uppercase tracking-wider text-slate-500">
              {formatDateTime(entry.createdAt)}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
