import { Link } from "react-router-dom";
import {
  ArrowRight,
  Building2,
  CalendarClock,
  IndianRupee,
  Stethoscope,
  UserRound,
  Users,
} from "lucide-react";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import { GlassCard } from "@/components/ui/GlassCard";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useAuth } from "@/providers/AuthProvider";
import { StatCard } from "@/components/enterprise/StatCard";

function formatGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function DashboardWelcome() {
  const { user } = useAuth();
  const { hospital, isLoading } = useDashboardData();

  return (
    <section className="rounded-xl border border-border-light bg-card p-6 shadow-card sm:p-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl space-y-3">
          <p className="text-sm font-medium uppercase tracking-wider text-muted">Hospital Command Center</p>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            {formatGreeting()}, {user?.first_name ?? "Administrator"}
          </h1>
          <p className="text-sm leading-relaxed text-muted sm:text-base">
            {isLoading ? (
              "Loading hospital overview…"
            ) : (
              <>
                Managing <span className="font-medium text-foreground">{hospital?.name ?? "your hospital"}</span>
                {hospital?.city ? ` · ${hospital.city}` : ""}. Monitor operations, organization health, and
                administrative workflows from one place.
              </>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full border border-border-light bg-surface px-3 py-1 text-xs text-muted">
            {new Date().toLocaleDateString(undefined, {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}
          </span>
          {hospital?.status && (
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs capitalize text-success">
              {hospital.status}
            </span>
          )}
        </div>
      </div>
    </section>
  );
}

export function HospitalKpiGrid() {
  const data = useDashboardData();

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Hospital overview</h2>
          <p className="text-sm text-muted">Live organization metrics from your tenant data</p>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Branches"
          value={data.branchCount}
          hint="Locations"
          icon={Building2}
          tone="accent"
          loading={data.isLoading}
        />
        <PermissionGuard permission="admin:departments">
          <StatCard
            label="Departments"
            value={data.departmentCount ?? "—"}
            hint="Clinical & admin units"
            icon={Users}
            tone="primary"
            loading={data.isLoading}
          />
        </PermissionGuard>
        <PermissionGuard permission="admin:staff">
          <StatCard
            label="Active staff"
            value={data.staffCount ?? "—"}
            hint="Employees"
            icon={Users}
            tone="secondary"
            loading={data.isLoading}
          />
        </PermissionGuard>
        <PermissionGuard permission="admin:doctors">
          <StatCard
            label="Doctors"
            value={data.doctorCount ?? "—"}
            hint={`${data.availableDoctors} available today`}
            icon={UserRound}
            tone="success"
            loading={data.isLoading}
          />
        </PermissionGuard>
        <PermissionGuard permission="patient:read">
          <StatCard
            label="Patients"
            value={data.patientCount ?? "—"}
            hint="Registered records"
            icon={Users}
            tone="primary"
            loading={data.isLoading}
          />
        </PermissionGuard>
      </div>
    </section>
  );
}

const clinicalModules = [
  {
    title: "Patients",
    description: "Registration, MRN, and patient records",
    icon: Users,
    status: "Live",
    to: "/patients",
    permission: "patient:read" as const,
  },
  {
    title: "Appointments",
    description: "OPD scheduling and visit workflow",
    icon: CalendarClock,
    status: "Sprint 8",
  },
  {
    title: "Revenue",
    description: "Billing, collections, and invoices",
    icon: IndianRupee,
    status: "Sprint 10",
  },
  {
    title: "OPD Queue",
    description: "Real-time outpatient queue board",
    icon: Stethoscope,
    status: "Sprint 9",
    to: "/opd/queue",
    permission: "opd:read" as const,
  },
];

export function ClinicalModulesPanel() {
  return (
    <GlassCard strong className="h-full">
      <h2 className="text-lg font-semibold text-foreground">Clinical operations</h2>
      <p className="mt-1 text-sm text-muted">
        Clinical modules become available as each sprint ships. Patient management is live in Sprint 7.
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {clinicalModules.map((module) => {
          const Icon = module.icon;
          const card = (
            <div
              key={module.title}
              className="rounded-xl border border-border-light bg-surface p-4 transition-colors hover:border-border hover:bg-hover"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-secondary">
                  <Icon className="h-5 w-5 text-muted" aria-hidden />
                </div>
                <span className="rounded-full border border-border-light bg-card px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted">
                  {module.status}
                </span>
              </div>
              <h3 className="mt-3 font-medium text-foreground">{module.title}</h3>
              <p className="mt-1 text-xs text-muted">{module.description}</p>
            </div>
          );

          if (module.to && module.permission) {
            return (
              <PermissionGuard key={module.title} permission={module.permission} fallback={card}>
                <Link to={module.to}>{card}</Link>
              </PermissionGuard>
            );
          }

          return card;
        })}
      </div>
    </GlassCard>
  );
}

export function QuickActionsPanel() {
  const actions = [
    { label: "Register patient", to: "/patients/new", permission: "patient:create" as const },
    { label: "Patient directory", to: "/patients", permission: "patient:read" as const },
    { label: "Invite user", to: "/admin/users", permission: "admin:users" as const },
    { label: "Add doctor", to: "/admin/doctors/new", permission: "admin:doctors" as const },
    { label: "Add staff", to: "/admin/staff/new", permission: "admin:staff" as const },
    { label: "Hospital settings", to: "/admin/settings", permission: "admin:settings" as const },
    { label: "System health", to: "/admin/health", permission: "admin:settings" as const },
    { label: "Manage branches", to: "/admin/branches", permission: "admin:settings" as const },
    { label: "Departments", to: "/admin/departments", permission: "admin:departments" as const },
  ];

  return (
    <GlassCard strong className="h-full">
      <h2 className="text-lg font-semibold text-foreground">Quick actions</h2>
      <p className="mt-1 text-sm text-muted">Frequently used administrative workflows</p>
      <div className="mt-5 space-y-2">
        {actions.map((action) => (
          <PermissionGuard key={action.label} permission={action.permission}>
            <Link
              to={action.to}
              className="group flex items-center justify-between rounded-lg border border-border-light bg-card px-4 py-3 text-sm transition-all hover:border-primary/30 hover:bg-blue-50"
            >
              <span className="font-medium text-foreground">{action.label}</span>
              <ArrowRight className="h-4 w-4 text-muted transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
            </Link>
          </PermissionGuard>
        ))}
      </div>
    </GlassCard>
  );
}
