import { ArrowLeft, AlertTriangle, Sparkles } from "lucide-react";
import { useState } from "react";

import { api } from "../api";
import { triggerLabels } from "../format";
import type { RfqCreateInput, TriggerType } from "../types";
import {
  cardClass,
  fieldClass,
  labelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from "../ui";

function toLocalInput(date: Date): string {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 16);
}

function minutesFromNow(minutes: number): string {
  return toLocalInput(new Date(Date.now() + minutes * 60_000));
}

function dateFromNow(days: number): string {
  const date = new Date(Date.now() + days * 86_400_000);
  return date.toISOString().slice(0, 10);
}

interface FormState {
  referenceId: string;
  title: string;
  pickupDate: string;
  bidStartTime: string;
  bidCloseTime: string;
  forcedCloseTime: string;
  isBritishAuction: boolean;
  triggerWindowMins: string;
  extensionDurationMins: string;
  extensionTrigger: TriggerType;
}

const initialState: FormState = {
  referenceId: "",
  title: "",
  pickupDate: dateFromNow(7),
  bidStartTime: minutesFromNow(5),
  bidCloseTime: minutesFromNow(35),
  forcedCloseTime: minutesFromNow(95),
  isBritishAuction: true,
  triggerWindowMins: "10",
  extensionDurationMins: "5",
  extensionTrigger: "ANY_RANK_CHANGE",
};

export function CreateRfqForm({
  onCreated,
  onCancel,
}: {
  onCreated: (id: string) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<FormState>(initialState);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const start = new Date(form.bidStartTime);
    const close = new Date(form.bidCloseTime);
    const forced = new Date(form.forcedCloseTime);

    if (!form.referenceId.trim() || !form.title.trim()) {
      setError("Reference ID and lane title are required.");
      return;
    }
    if (Number.isNaN(start.getTime()) || Number.isNaN(close.getTime())) {
      setError("Bid start and close times must be valid.");
      return;
    }
    if (!(start < close)) {
      setError("Bid close time must be after the bid start time.");
      return;
    }
    if (!(close < forced)) {
      setError("Forced close time must be later than the bid close time.");
      return;
    }

    const windowMinutes = Number(form.triggerWindowMins);
    const extensionMinutes = Number(form.extensionDurationMins);
    if (
      !Number.isInteger(windowMinutes) ||
      windowMinutes < 1 ||
      !Number.isInteger(extensionMinutes) ||
      extensionMinutes < 1
    ) {
      setError("Trigger window and extension duration must be positive whole minutes.");
      return;
    }

    const payload: RfqCreateInput = {
      referenceId: form.referenceId.trim(),
      title: form.title.trim(),
      pickupDate: new Date(`${form.pickupDate}T12:00:00`).toISOString(),
      bidStartTime: start.toISOString(),
      bidCloseTime: close.toISOString(),
      forcedCloseTime: forced.toISOString(),
      isBritishAuction: form.isBritishAuction,
      triggerWindowMins: windowMinutes,
      extensionDurationMins: extensionMinutes,
      extensionTrigger: form.extensionTrigger,
    };

    setBusy(true);
    try {
      const result = await api.createRfq(payload);
      onCreated(result.data.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not create the RFQ.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-3xl space-y-5">
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex items-center gap-1.5 text-sm text-slate-400 transition hover:text-slate-100"
        >
          <ArrowLeft size={16} />
          Back to auctions
        </button>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-sky-400/30 bg-sky-400/10 px-3 py-1 text-[11px] text-sky-200">
          <Sparkles size={12} />
          British auction RFQ
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className={cardClass}>
          <h1 className="text-lg font-semibold text-slate-50">RFQ details</h1>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label className={labelClass} htmlFor="referenceId">
                Reference ID
              </label>
              <input
                id="referenceId"
                className={fieldClass}
                value={form.referenceId}
                onChange={(event) => update("referenceId", event.target.value)}
                placeholder="RFQ-2026-005"
                required
                minLength={3}
                maxLength={50}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="pickupDate">
                Pickup / service date
              </label>
              <input
                id="pickupDate"
                type="date"
                className={fieldClass}
                value={form.pickupDate}
                onChange={(event) => update("pickupDate", event.target.value)}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className={labelClass} htmlFor="title">
                Lane / title
              </label>
              <input
                id="title"
                className={fieldClass}
                value={form.title}
                onChange={(event) => update("title", event.target.value)}
                placeholder="Shanghai to Rotterdam | 40ft HC"
                required
                minLength={3}
                maxLength={255}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="bidStartTime">
                Bid start
              </label>
              <input
                id="bidStartTime"
                type="datetime-local"
                className={fieldClass}
                value={form.bidStartTime}
                onChange={(event) => update("bidStartTime", event.target.value)}
                required
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="bidCloseTime">
                Bid close
              </label>
              <input
                id="bidCloseTime"
                type="datetime-local"
                className={fieldClass}
                value={form.bidCloseTime}
                onChange={(event) => update("bidCloseTime", event.target.value)}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className={labelClass} htmlFor="forcedCloseTime">
                Forced close (hard ceiling)
              </label>
              <input
                id="forcedCloseTime"
                type="datetime-local"
                className={fieldClass}
                value={form.forcedCloseTime}
                onChange={(event) => update("forcedCloseTime", event.target.value)}
                required
              />
              <p className="mt-1.5 text-[11px] text-slate-500">
                Bidding stops here regardless of any extension. Must be later than
                the bid close time.
              </p>
            </div>
          </div>
        </div>

        <div className={cardClass}>
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-slate-50">
              British auction rules
            </h2>
            <label className="inline-flex cursor-pointer items-center gap-2 text-xs text-slate-300">
              <input
                type="checkbox"
                className="h-4 w-4 accent-sky-500"
                checked={form.isBritishAuction}
                onChange={(event) =>
                  update("isBritishAuction", event.target.checked)
                }
              />
              Enable auto-extension
            </label>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div>
              <label className={labelClass} htmlFor="triggerWindowMins">
                Trigger window X (min)
              </label>
              <input
                id="triggerWindowMins"
                type="number"
                min={1}
                max={1440}
                className={fieldClass}
                value={form.triggerWindowMins}
                onChange={(event) =>
                  update("triggerWindowMins", event.target.value)
                }
                disabled={!form.isBritishAuction}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="extensionDurationMins">
                Extension Y (min)
              </label>
              <input
                id="extensionDurationMins"
                type="number"
                min={1}
                max={1440}
                className={fieldClass}
                value={form.extensionDurationMins}
                onChange={(event) =>
                  update("extensionDurationMins", event.target.value)
                }
                disabled={!form.isBritishAuction}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="extensionTrigger">
                Extension trigger
              </label>
              <select
                id="extensionTrigger"
                className={fieldClass}
                value={form.extensionTrigger}
                onChange={(event) =>
                  update("extensionTrigger", event.target.value as TriggerType)
                }
                disabled={!form.isBritishAuction}
              >
                {Object.entries(triggerLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <p className="mt-3 text-[11px] text-slate-500">
            A qualifying bid inside the last X minutes moves the close time
            forward by Y minutes, never past the forced close.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-2">
          <button type="button" onClick={onCancel} className={secondaryButtonClass}>
            Cancel
          </button>
          <button type="submit" className={primaryButtonClass} disabled={busy}>
            {busy ? "Creating…" : "Create auction"}
          </button>
        </div>
      </form>
    </section>
  );
}
