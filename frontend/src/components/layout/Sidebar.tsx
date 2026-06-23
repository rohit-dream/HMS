import { NavLink } from "react-router-dom";
import { PermissionGuard } from "@/components/shared/PermissionGuard";

const navItems = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "OPD", to: "/opd/queue", permission: "opd:read" as const },
  { label: "Billing", to: "/billing/collection", permission: "billing:read" as const },
  { label: "Settings", to: "/admin/settings", permission: "admin:settings" as const },
  { label: "Branches", to: "/admin/branches", permission: "admin:settings" as const },
  { label: "Departments", to: "/admin/departments", permission: "admin:departments" as const },
  { label: "Staff", to: "/admin/staff", permission: "admin:staff" as const },
  { label: "Doctors", to: "/admin/doctors", permission: "admin:doctors" as const },
  { label: "Users", to: "/admin/users", permission: "admin:users" as const },
];

export function Sidebar() {
  return (
    <aside className="flex w-sidebar shrink-0 flex-col bg-sidebar text-white">
      <div className="border-b border-white/10 px-4 py-5">
        <p className="text-lg font-semibold">HMS Platform</p>
        <p className="text-xs text-white/60">Hospital Admin</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {navItems.map((item) => {
          const link = (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive ? "bg-primary text-white" : "text-white/80 hover:bg-white/10"
                }`
              }
              end={item.to === "/dashboard"}
            >
              {item.label}
            </NavLink>
          );

          if (!item.permission) {
            return link;
          }

          return (
            <PermissionGuard key={item.label} permission={item.permission}>
              {link}
            </PermissionGuard>
          );
        })}
      </nav>
    </aside>
  );
}
