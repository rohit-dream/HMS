import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Info, UserPlus } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { useDashboardData } from "@/hooks/useDashboardData";
import { PermissionGuard } from "@/components/shared/PermissionGuard";

interface AlertItem {
  id: string;
  tone: "warning" | "info" | "success";
  title: string;
  description: string;
  href?: string;
  permission?: string;
}

export function AlertsPanel() {
  const data = useDashboardData();
  const alerts: AlertItem[] = [];

  if (data.canViewDepartments && data.departmentCount === 0) {
    alerts.push({
      id: "no-departments",
      tone: "warning",
      title: "Set up departments",
      description: "Create clinical and administrative departments before assigning staff.",
      href: "/admin/departments",
      permission: "admin:departments",
    });
  }

  if (data.canViewDoctors && data.doctorCount === 0) {
    alerts.push({
      id: "no-doctors",
      tone: "warning",
      title: "Add doctor profiles",
      description: "Configure doctors and schedules to prepare for OPD workflows.",
      href: "/admin/doctors/new",
      permission: "admin:doctors",
    });
  }

  if (data.canViewDoctors && (data.doctorCount ?? 0) > 0 && data.availableDoctors === 0) {
    alerts.push({
      id: "no-available-doctors",
      tone: "info",
      title: "No doctors marked available",
      description: "Update doctor availability so front desk can book consultations.",
      href: "/admin/doctors",
      permission: "admin:doctors",
    });
  }

  if (data.branchCount <= 1) {
    alerts.push({
      id: "single-branch",
      tone: "info",
      title: "Multi-branch setup",
      description: "Add additional branches if your hospital operates at multiple locations.",
      href: "/admin/branches",
      permission: "admin:settings",
    });
  }

  if (alerts.length === 0) {
    alerts.push({
      id: "healthy",
      tone: "success",
      title: "Organization baseline complete",
      description: "Core admin structure looks configured. Clinical modules will extend this dashboard.",
    });
  }

  const toneIcon = {
    warning: AlertTriangle,
    info: Info,
    success: CheckCircle2,
  };

  const toneClass = {
    warning: "border-amber-200 bg-amber-50 text-warning",
    info: "border-blue-200 bg-blue-50 text-primary",
    success: "border-emerald-200 bg-emerald-50 text-success",
  };

  return (
    <GlassCard strong className="h-full">
      <h2 className="text-lg font-semibold text-foreground">Alerts & recommendations</h2>
      <p className="mt-1 text-sm text-muted">Actionable setup guidance for your hospital</p>
      <ul className="mt-5 space-y-3">
        {alerts.map((alert) => {
          const Icon = toneIcon[alert.tone];
          const content = (
            <li
              key={alert.id}
              className={`flex gap-3 rounded-xl border p-4 ${toneClass[alert.tone]}`}
            >
              <Icon className="mt-0.5 h-5 w-5 shrink-0 opacity-80" aria-hidden />
              <div>
                <p className="font-medium">{alert.title}</p>
                <p className="mt-1 text-sm opacity-90">{alert.description}</p>
              </div>
            </li>
          );

          if (alert.href && alert.permission) {
            return (
              <PermissionGuard key={alert.id} permission={alert.permission}>
                <Link to={alert.href} className="block transition-opacity hover:opacity-90">
                  {content}
                </Link>
              </PermissionGuard>
            );
          }

          return content;
        })}
      </ul>
    </GlassCard>
  );
}

export function RecentActivityPanel() {
  const data = useDashboardData();

  return (
    <GlassCard strong className="h-full">
      <h2 className="text-lg font-semibold text-foreground">Recent team activity</h2>
      <p className="mt-1 text-sm text-muted">Latest user sign-ins across your hospital tenant</p>

      {!data.canViewUsers ? (
        <p className="mt-6 text-sm text-muted">User activity requires admin:users permission.</p>
      ) : data.isLoading ? (
        <div className="mt-6 space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-12 animate-pulse rounded-lg bg-surface-secondary" />
          ))}
        </div>
      ) : data.recentUsers.length === 0 ? (
        <p className="mt-6 text-sm text-muted">No users found yet.</p>
      ) : (
        <ul className="mt-5 divide-y divide-border-light">
          {data.recentUsers.map((member) => (
            <li key={member.id} className="flex items-center gap-3 py-3 first:pt-0">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-sm font-semibold text-primary">
                {member.first_name.charAt(0)}
                {member.last_name.charAt(0)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-foreground">
                  {member.first_name} {member.last_name}
                </p>
                <p className="truncate text-xs text-muted">{member.email}</p>
              </div>
              <div className="text-right text-xs text-muted">
                {member.last_login_at
                  ? new Date(member.last_login_at).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "Never signed in"}
              </div>
            </li>
          ))}
        </ul>
      )}

      <PermissionGuard permission="admin:users">
        <Link
          to="/admin/users"
          className="mt-4 inline-flex items-center gap-2 text-sm text-primary hover:text-primary/80"
        >
          <UserPlus className="h-4 w-4" aria-hidden />
          Manage all users
        </Link>
      </PermissionGuard>
    </GlassCard>
  );
}

export function DoctorAvailabilityPanel() {
  const data = useDashboardData();

  if (!data.canViewDoctors) return null;

  const total = data.doctorCount ?? 0;
  const available = data.availableDoctors;
  const unavailable = Math.max(total - available, 0);
  const availabilityRate = total > 0 ? Math.round((available / total) * 100) : 0;

  return (
    <GlassCard strong>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Doctor availability</h2>
          <p className="mt-1 text-sm text-muted">Consultation readiness across your medical staff</p>
        </div>
        <Link to="/admin/doctors" className="text-sm text-primary hover:text-primary/80">
          Manage doctors
        </Link>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_12rem] lg:items-center">
        <div className="space-y-4">
          <div>
            <div className="mb-2 flex justify-between text-sm">
              <span className="text-muted">Availability rate</span>
              <span className="font-medium text-foreground">{availabilityRate}%</span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-surface-secondary">
              <div
                className="h-full rounded-full bg-primary transition-all duration-500"
                style={{ width: `${availabilityRate}%` }}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
              <p className="text-muted">Available</p>
              <p className="text-2xl font-semibold text-success">{available}</p>
            </div>
            <div className="rounded-lg border border-border-light bg-card p-3">
              <p className="text-muted">Unavailable</p>
              <p className="text-2xl font-semibold text-foreground">{unavailable}</p>
            </div>
          </div>
        </div>
        <div className="flex h-32 w-32 items-center justify-center justify-self-center rounded-full border border-border-light bg-surface">
          <div className="text-center">
            <p className="text-3xl font-bold text-foreground">{total}</p>
            <p className="text-xs text-muted">Total doctors</p>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
