import { Clock } from "lucide-react";
import { useEffect, useState } from "react";

import { formatDuration } from "../format";
import type { AuctionStatus } from "../types";

interface CountdownProps {
  target: string;
  now: () => number;
  windowMinutes?: number;
  status?: AuctionStatus;
  variant?: "lg" | "sm";
}

export function Countdown({
  target,
  now,
  windowMinutes,
  status,
  variant = "sm",
}: CountdownProps) {
  const [, setTick] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => setTick((value) => value + 1), 250);
    return () => window.clearInterval(timer);
  }, []);

  const remaining = Math.max(0, Date.parse(target) - now());
  const running = status === undefined || status === "ACTIVE";
  const inWindow =
    running &&
    windowMinutes !== undefined &&
    remaining > 0 &&
    remaining <= windowMinutes * 60_000;
  const closed = remaining === 0 || !running;

  if (variant === "sm") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 text-xs ${
          closed ? "text-slate-500" : inWindow ? "text-amber-300" : "text-slate-300"
        }`}
      >
        <Clock size={13} />
        {closed ? "Closed" : formatDuration(remaining)}
        {inWindow && <span className="text-amber-400/80">· window</span>}
      </span>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.18em] text-slate-400">
        <Clock size={14} />
        {closed ? "Bidding closed" : "Bid closes in"}
      </div>
      <div
        className={`mt-2 font-mono text-4xl font-semibold tabular-nums ${
          closed ? "text-slate-500" : inWindow ? "text-amber-300" : "text-slate-50"
        }`}
      >
        {formatDuration(remaining)}
      </div>
      {inWindow && (
        <p className="mt-2 text-xs text-amber-300/90">
          Inside the {windowMinutes}-minute trigger window — qualifying bids
          extend the close time.
        </p>
      )}
    </div>
  );
}
