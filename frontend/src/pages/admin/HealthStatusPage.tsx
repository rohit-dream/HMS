import { useQuery } from "@tanstack/react-query";
import { Activity, Database, Server } from "lucide-react";
import { getHealth, getReady } from "@/api/endpoints/health";
import { AdminPageFrame } from "@/components/enterprise";
import { Badge } from "@/components/ui";
import { GlassCard } from "@/components/ui/GlassCard";

function statusVariant(status: string): "success" | "warning" | "error" | "neutral" {
  const normalized = status.toLowerCase();
  if (normalized === "ok" || normalized === "healthy" || normalized === "ready") {
    return "success";
  }
  if (normalized === "degraded") {
    return "warning";
  }
  if (normalized === "error" || normalized === "unhealthy" || normalized === "not_ready") {
    return "error";
  }
  return "neutral";
}

export function HealthStatusPage() {
  const healthQuery = useQuery({
    queryKey: ["system", "health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });

  const readyQuery = useQuery({
    queryKey: ["system", "ready"],
    queryFn: getReady,
    refetchInterval: 30_000,
  });

  const health = healthQuery.data;
  const ready = readyQuery.data;

  return (
    <AdminPageFrame
      title="System health"
      description="Live API liveness and dependency readiness for this deployment."
    >
      <div className="grid gap-4 md:grid-cols-2">
        <GlassCard strong className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-secondary">
              <Server className="h-5 w-5 text-muted" aria-hidden />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">API liveness</h2>
              <p className="text-sm text-muted">GET /health</p>
            </div>
          </div>
          {healthQuery.isLoading ? (
            <p className="text-sm text-muted">Checking service status…</p>
          ) : healthQuery.isError ? (
            <p className="text-sm text-error">Unable to reach the health endpoint.</p>
          ) : (
            <dl className="grid gap-3 text-sm">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted">Status</dt>
                <dd>
                  <Badge variant={statusVariant(health?.status ?? "")}>{health?.status ?? "—"}</Badge>
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted">Service</dt>
                <dd className="font-medium text-foreground">{health?.service ?? "—"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted">Version</dt>
                <dd className="font-medium text-foreground">{health?.version ?? "—"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted">Environment</dt>
                <dd className="font-medium text-foreground">{health?.environment ?? "—"}</dd>
              </div>
            </dl>
          )}
        </GlassCard>

        <GlassCard strong className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-secondary">
              <Activity className="h-5 w-5 text-muted" aria-hidden />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">Readiness</h2>
              <p className="text-sm text-muted">GET /health/ready</p>
            </div>
          </div>
          {readyQuery.isLoading ? (
            <p className="text-sm text-muted">Checking dependencies…</p>
          ) : readyQuery.isError ? (
            <p className="text-sm text-error">Unable to reach the readiness endpoint.</p>
          ) : (
            <dl className="grid gap-3 text-sm">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted">Overall</dt>
                <dd>
                  <Badge variant={statusVariant(ready?.status ?? "")}>{ready?.status ?? "—"}</Badge>
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="flex items-center gap-2 text-muted">
                  <Database className="h-4 w-4" aria-hidden />
                  Database
                </dt>
                <dd>
                  <Badge variant={statusVariant(ready?.checks.database ?? "")}>
                    {ready?.checks.database ?? "—"}
                  </Badge>
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted">Redis</dt>
                <dd>
                  <Badge variant={statusVariant(ready?.checks.redis ?? "")}>
                    {ready?.checks.redis ?? "—"}
                  </Badge>
                </dd>
              </div>
            </dl>
          )}
        </GlassCard>
      </div>
    </AdminPageFrame>
  );
}
