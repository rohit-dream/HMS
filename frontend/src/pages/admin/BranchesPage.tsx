import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createLocationRequest,
  listLocationsRequest,
  updateLocationRequest,
} from "@/api/endpoints/hospital";
import { ApiError } from "@/api/errors";
import type { HospitalLocation } from "@/api/types/hospital";
import {
  alertErrorClassName,
  alertSuccessClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";

export function BranchesPage() {
  const queryClient = useQueryClient();
  const locationsQuery = useQuery({
    queryKey: ["hospital", "locations"],
    queryFn: listLocationsRequest,
  });

  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [city, setCity] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: createLocationRequest,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital", "locations"] });
      setName("");
      setCode("");
      setCity("");
      setPhone("");
      setSuccess("Branch created.");
      setError(null);
    },
    onError: (err) => {
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to create branch.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, phone: branchPhone }: { id: string; phone: string }) =>
      updateLocationRequest(id, { phone: branchPhone || undefined }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital", "locations"] });
      setSuccess("Branch updated.");
      setError(null);
    },
    onError: (err) => {
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to update branch.");
    },
  });

  function handleCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    createMutation.mutate({
      name: name.trim(),
      code: code.trim().toUpperCase(),
      city: city.trim() || undefined,
      phone: phone.trim() || undefined,
    });
  }

  const locations = locationsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Branches</h2>
        <p className="mt-1 text-sm text-muted">Manage hospital locations and branch codes.</p>
      </div>

      {error && <p className={alertErrorClassName}>{error}</p>}
      {success && <p className={alertSuccessClassName}>{success}</p>}

      <form
        className="grid gap-4 rounded-lg border border-border bg-white p-6 sm:grid-cols-2"
        onSubmit={handleCreate}
      >
        <h3 className="sm:col-span-2 text-lg font-medium text-slate-900">Add branch</h3>
        <label className={labelClassName}>
          <span className={labelTextClassName}>Name</span>
          <input className={inputClassName} value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label className={labelClassName}>
          <span className={labelTextClassName}>Code</span>
          <input
            className={inputClassName}
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            required
          />
        </label>
        <label className={labelClassName}>
          <span className={labelTextClassName}>City</span>
          <input className={inputClassName} value={city} onChange={(e) => setCity(e.target.value)} />
        </label>
        <label className={labelClassName}>
          <span className={labelTextClassName}>Phone</span>
          <input className={inputClassName} value={phone} onChange={(e) => setPhone(e.target.value)} />
        </label>
        <div className="sm:col-span-2">
          <button type="submit" disabled={createMutation.isPending} className={primaryButtonClassName}>
            {createMutation.isPending ? "Creating…" : "Create branch"}
          </button>
        </div>
      </form>

      <div className="overflow-hidden rounded-lg border border-border bg-white">
        <table className="min-w-full text-sm">
          <thead className="border-b border-border bg-surface/60 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Code</th>
              <th className="px-4 py-3 font-medium">City</th>
              <th className="px-4 py-3 font-medium">Phone</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {locationsQuery.isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-muted">
                  Loading branches…
                </td>
              </tr>
            )}
            {locations.map((location) => (
              <BranchRow
                key={location.id}
                location={location}
                onSavePhone={(branchPhone) =>
                  updateMutation.mutate({ id: location.id, phone: branchPhone })
                }
                saving={updateMutation.isPending}
              />
            ))}
            {!locationsQuery.isLoading && locations.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-muted">
                  No branches yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function BranchRow({
  location,
  onSavePhone,
  saving,
}: {
  location: HospitalLocation;
  onSavePhone: (phone: string) => void;
  saving: boolean;
}) {
  const [phone, setPhone] = useState(location.phone ?? "");

  return (
    <tr className="border-b border-border last:border-0">
      <td className="px-4 py-3">
        {location.name}
        {location.is_primary && (
          <span className="ml-2 rounded bg-primary/10 px-2 py-0.5 text-xs text-primary">Primary</span>
        )}
      </td>
      <td className="px-4 py-3 font-mono text-xs">{location.code}</td>
      <td className="px-4 py-3">{location.city ?? "—"}</td>
      <td className="px-4 py-3">
        <div className="flex gap-2">
          <input
            className="w-full min-w-[8rem] rounded border border-border px-2 py-1"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <button
            type="button"
            disabled={saving || phone === (location.phone ?? "")}
            onClick={() => onSavePhone(phone)}
            className="shrink-0 rounded border border-border px-2 py-1 text-xs hover:bg-surface disabled:opacity-50"
          >
            Save
          </button>
        </div>
      </td>
      <td className="px-4 py-3 capitalize">{location.is_active ? "active" : "inactive"}</td>
    </tr>
  );
}
