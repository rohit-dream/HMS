import { NavLink } from "react-router-dom";
import {
  Building2,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  FlaskConical,
  LayoutDashboard,
  Layers,
  Pill,
  Settings,
  Stethoscope,
  UserCog,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import { useSidebar } from "@/components/layout/SidebarContext";
import { cn } from "@/lib/cn";

interface NavItem {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
  permission?: string;
  end?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: "Overview",
    items: [{ label: "Command Center", to: "/dashboard", icon: LayoutDashboard, end: true }],
  },
  {
    label: "Clinical",
    items: [
      { label: "Patients", to: "/patients", icon: UserRound, permission: "patient:read" },
      { label: "OPD Queue", to: "/opd/queue", icon: Stethoscope, permission: "opd:read" },
      { label: "Appointments", to: "/appointments", icon: CalendarDays, permission: "appointment:read" },
      { label: "IPD", to: "/ipd/admissions", icon: Users, permission: "ipd:read" },
      { label: "Pharmacy", to: "/pharmacy/queue", icon: Pill, permission: "pharmacy:read" },
      { label: "Laboratory", to: "/lab/orders", icon: FlaskConical, permission: "lab:read" },
    ],
  },
  {
    label: "Administration",
    items: [
      { label: "Hospital Settings", to: "/admin/settings", icon: Settings, permission: "admin:settings" },
      { label: "Branches", to: "/admin/branches", icon: Building2, permission: "admin:settings" },
      { label: "Departments", to: "/admin/departments", icon: Layers, permission: "admin:departments" },
      { label: "Staff", to: "/admin/staff", icon: Users, permission: "admin:staff" },
      { label: "Doctors", to: "/admin/doctors", icon: UserRound, permission: "admin:doctors" },
      { label: "Users & Roles", to: "/admin/users", icon: UserCog, permission: "admin:users" },
    ],
  },
  {
    label: "Finance",
    items: [
      { label: "Collections", to: "/billing/collection", icon: CreditCard, permission: "billing:read" },
    ],
  },
];

function SidebarNav({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4">
      {navGroups.map((group) => (
        <div key={group.label}>
          {!collapsed && (
            <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
              {group.label}
            </p>
          )}
          <div className="space-y-1">
            {group.items.map((item) => {
              const Icon = item.icon;
              const link = (
                <NavLink
                  key={item.label}
                  to={item.to}
                  title={collapsed ? item.label : undefined}
                  onClick={onNavigate}
                  end={item.end}
                  className={({ isActive }) =>
                    cn(
                      "glass-nav-link group relative",
                      collapsed && "justify-center px-2",
                      isActive && "glass-nav-link-active",
                    )
                  }
                >
                  <Icon className="h-[18px] w-[18px] shrink-0" aria-hidden />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                  {collapsed && (
                    <span className="pointer-events-none absolute left-full z-50 ml-2 hidden whitespace-nowrap rounded-lg bg-slate-900 px-2 py-1 text-xs text-white shadow-lg group-hover:block">
                      {item.label}
                    </span>
                  )}
                </NavLink>
              );

              if (!item.permission) return link;

              return (
                <PermissionGuard key={item.label} permission={item.permission}>
                  {link}
                </PermissionGuard>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

function SidebarChrome({
  collapsed,
  onToggleCollapsed,
  onMobileClose,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onMobileClose?: () => void;
}) {
  return (
    <>
      <div
        className={cn(
          "flex h-16 items-center border-b border-gray-700 px-3",
          collapsed ? "justify-center" : "justify-between",
        )}
      >
        {!collapsed && (
          <div className="min-w-0 px-1">
            <p className="truncate text-base font-bold text-white">HMS Platform</p>
            <p className="truncate text-[11px] text-sidebar-text">Enterprise Healthcare</p>
          </div>
        )}
        <div className="flex items-center gap-1">
          {onMobileClose && (
            <button
              type="button"
              className="rounded-lg p-2 text-sidebar-text hover:bg-sidebar-active lg:hidden"
              onClick={onMobileClose}
              aria-label="Close navigation"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          <button
            type="button"
            className="hidden rounded-lg p-2 text-sidebar-text hover:bg-sidebar-active lg:inline-flex"
            onClick={onToggleCollapsed}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </>
  );
}

export function Sidebar() {
  const { collapsed, mobileOpen, toggleCollapsed, setMobileOpen } = useSidebar();

  const desktop = (
    <aside
      className={cn(
        "glass-sidebar sticky top-0 hidden h-screen shrink-0 flex-col transition-[width] duration-300 lg:flex",
        collapsed ? "w-sidebar-collapsed" : "w-sidebar",
      )}
    >
      <SidebarChrome collapsed={collapsed} onToggleCollapsed={toggleCollapsed} />
      <SidebarNav collapsed={collapsed} />
    </aside>
  );

  const mobile =
    mobileOpen ? (
      <div className="fixed inset-0 z-40 lg:hidden">
        <button
          type="button"
          className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
        <aside className="glass-sidebar absolute inset-y-0 left-0 flex w-sidebar max-w-[88vw] flex-col shadow-card-md">
          <SidebarChrome
            collapsed={false}
            onToggleCollapsed={toggleCollapsed}
            onMobileClose={() => setMobileOpen(false)}
          />
          <SidebarNav collapsed={false} onNavigate={() => setMobileOpen(false)} />
        </aside>
      </div>
    ) : null;

  return (
    <>
      {desktop}
      {mobile}
    </>
  );
}
