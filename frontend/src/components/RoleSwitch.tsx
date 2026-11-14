import type { Role } from "../types";

const options: { value: Role; label: string }[] = [
  { value: "buyer", label: "Buyer" },
  { value: "supplier", label: "Supplier" },
];

export function RoleSwitch({
  role,
  onChange,
}: {
  role: Role;
  onChange: (role: Role) => void;
}) {
  return (
    <div
      className="inline-flex rounded-full border border-white/10 bg-slate-900/80 p-0.5"
      role="group"
      aria-label="Workspace role"
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          aria-pressed={role === option.value}
          className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
            role === option.value
              ? "bg-slate-100 text-slate-900"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
