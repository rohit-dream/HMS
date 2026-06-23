import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getHealth, getReady } from "@/api/endpoints/health";
import { NetworkError } from "@/api/errors";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import { useAuth } from "@/providers/AuthProvider";

function StatusBadge({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${
        ok ? "bg-green-100 text-success" : "bg-red-100 text-error"
      }`}
    >
      {label}: {ok ? "Connected" : "Disconnected"}
    </span>
  );
}

export function HomePage() {
  const { user, permissions } = useAuth();
  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });

  const readyQuery = useQuery({
    queryKey: ["ready"],
    queryFn: getReady,
    retry: false,
  });

  const apiOk = healthQuery.isSuccess;
  const readyOk = readyQuery.isSuccess && readyQuery.data?.status === "ready";
  const errorMessage =
    healthQuery.error instanceof NetworkError
      ? healthQuery.error.message
      : healthQuery.error instanceof Error
        ? healthQuery.error.message
        : null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Dashboard</h2>
        <p className="mt-1 text-muted">
          {user
            ? `Welcome back, ${user.first_name}. You have ${permissions.length} permission(s) from /auth/me.`
            : "Foundation shell with authenticated session."}
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <StatusBadge label="API Liveness" ok={apiOk} />
        <StatusBadge label="API Readiness" ok={readyOk} />
      </div>

      {healthQuery.isLoading && <p className="text-sm text-muted">Checking API health…</p>}
      {errorMessage && <p className="text-sm text-error">{errorMessage}</p>}

      {healthQuery.data && (
        <div className="rounded-lg border border-border bg-white p-4 text-sm">
          <p>
            <span className="font-medium">Service:</span> {healthQuery.data.service}
          </p>
          <p>
            <span className="font-medium">Version:</span> {healthQuery.data.version}
          </p>
          <p>
            <span className="font-medium">Environment:</span> {healthQuery.data.environment}
          </p>
        </div>
      )}

      <div className="rounded-lg border border-border bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-900">Quick actions</h3>
        <p className="mt-1 text-xs text-muted">
          Actions below are shown only when your account has the matching permission.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <PermissionGuard permission="admin:users">
            <Link
              to="/admin/users"
              className="rounded-md bg-primary/10 px-3 py-1.5 text-sm text-primary hover:bg-primary/20"
            >
              Manage users
            </Link>
          </PermissionGuard>
          <PermissionGuard permission="admin:settings">
            <Link
              to="/admin/settings"
              className="rounded-md bg-primary/10 px-3 py-1.5 text-sm text-primary hover:bg-primary/20"
            >
              Hospital settings
            </Link>
          </PermissionGuard>
          <PermissionGuard permission="patient:create">
            <span className="rounded-md bg-primary/10 px-3 py-1.5 text-sm text-primary">
              Register patient
            </span>
          </PermissionGuard>
          <PermissionGuard permission="billing:void">
            <span className="rounded-md bg-primary/10 px-3 py-1.5 text-sm text-primary">
              Void invoice
            </span>
          </PermissionGuard>
        </div>
      </div>
    </div>
  );
}
