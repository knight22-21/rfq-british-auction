import { Gavel, Plus } from "lucide-react";
import { useEffect, useState } from "react";

import { AuctionDetail } from "./components/AuctionDetail";
import { AuctionList } from "./components/AuctionList";
import { CreateRfqForm } from "./components/CreateRfqForm";
import { RoleSwitch } from "./components/RoleSwitch";
import { useServerClock } from "./hooks/useServerClock";
import type { Role } from "./types";
import { fieldClass } from "./ui";

type View =
  | { name: "list" }
  | { name: "detail"; id: string }
  | { name: "create" };

function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Private browsing modes can block storage; the session still works.
  }
}

export default function App() {
  const [role, setRole] = useState<Role>(() =>
    readStorage("rfq.role") === "supplier" ? "supplier" : "buyer",
  );
  const [carrierName, setCarrierName] = useState(
    () => readStorage("rfq.carrier") ?? "",
  );
  const [view, setView] = useState<View>({ name: "list" });
  const { now, sync } = useServerClock();

  useEffect(() => {
    writeStorage("rfq.role", role);
  }, [role]);

  useEffect(() => {
    writeStorage("rfq.carrier", carrierName);
  }, [carrierName]);

  useEffect(() => {
    if (role === "supplier" && view.name === "create") {
      setView({ name: "list" });
    }
  }, [role, view.name]);

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3">
          <button
            type="button"
            onClick={() => setView({ name: "list" })}
            className="flex items-center gap-2 text-left"
          >
            <span className="grid h-9 w-9 place-items-center rounded-lg border border-sky-400/20 bg-sky-400/10 text-sky-300">
              <Gavel size={18} />
            </span>
            <span>
              <span className="block text-sm font-semibold text-slate-100">
                RFQ Auction Desk
              </span>
              <span className="block text-[11px] text-slate-500">
                British auction bidding room
              </span>
            </span>
          </button>

          <div className="ml-auto flex flex-wrap items-center gap-2.5">
            {role === "supplier" && (
              <input
                value={carrierName}
                onChange={(event) => setCarrierName(event.target.value)}
                placeholder="Carrier name"
                maxLength={100}
                aria-label="Carrier name"
                className={`${fieldClass} w-40 py-1.5 text-xs`}
              />
            )}
            <RoleSwitch role={role} onChange={setRole} />
            {role === "buyer" && view.name !== "create" && (
              <button
                type="button"
                onClick={() => setView({ name: "create" })}
                className="inline-flex items-center gap-1.5 rounded-lg bg-sky-500 px-3 py-2 text-xs font-semibold text-slate-950 transition hover:bg-sky-400"
              >
                <Plus size={14} />
                New RFQ
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {view.name === "list" && (
          <AuctionList
            role={role}
            now={now}
            sync={sync}
            onOpen={(id) => setView({ name: "detail", id })}
            onCreate={() => setView({ name: "create" })}
          />
        )}

        {view.name === "detail" && (
          <AuctionDetail
            id={view.id}
            role={role}
            carrierName={carrierName}
            onCarrierNameChange={setCarrierName}
            onBack={() => setView({ name: "list" })}
            now={now}
            sync={sync}
          />
        )}

        {view.name === "create" && role === "buyer" && (
          <CreateRfqForm
            onCreated={(id) => setView({ name: "detail", id })}
            onCancel={() => setView({ name: "list" })}
          />
        )}
      </main>

      <footer className="mx-auto max-w-7xl px-4 pb-8 text-[11px] text-slate-600">
        Bid times are stored in UTC and rendered in your local timezone.
      </footer>
    </div>
  );
}
