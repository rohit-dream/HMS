import { useQuery } from "@tanstack/react-query";
import { getHealth, getReady } from "@/api/endpoints/health";
import { NetworkError } from "@/api/errors";

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
        <h2 className="text-2xl font-semibold text-slate-900">Sprint 1 — Foundation</h2>
        <p className="mt-1 text-muted">
          Project scaffold is running. Business modules and authentication ship in later sprints.
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
    </div>
  );
}
