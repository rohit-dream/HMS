import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Dashboard", to: "/", disabled: false },
  { label: "Patients", to: "#", disabled: true },
  { label: "OPD", to: "#", disabled: true },
  { label: "Billing", to: "#", disabled: true },
  { label: "Admin", to: "#", disabled: true },
];

export function Sidebar() {
  return (
    <aside className="flex w-sidebar shrink-0 flex-col bg-sidebar text-white">
      <div className="border-b border-white/10 px-4 py-5">
        <p className="text-lg font-semibold">HMS Platform</p>
        <p className="text-xs text-white/60">Sprint 1 Foundation</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {navItems.map((item) =>
          item.disabled ? (
            <span
              key={item.label}
              className="cursor-not-allowed rounded-md px-3 py-2 text-sm text-white/40"
            >
              {item.label}
            </span>
          ) : (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive ? "bg-primary text-white" : "text-white/80 hover:bg-white/10"
                }`
              }
              end
            >
              {item.label}
            </NavLink>
          ),
        )}
      </nav>
    </aside>
  );
}
