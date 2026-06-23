import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  assignRoleRequest,
  disableUserRequest,
  getUserRequest,
  removeRoleRequest,
  updateUserRequest,
} from "@/api/endpoints/admin-users";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  alertSuccessClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import { TENANT_ROLE_OPTIONS } from "@/lib/admin-constants";
import { useAuth } from "@/providers/AuthProvider";

export function UserDetailPage() {
  const { userId } = useParams<{ userId: string }>();
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();

  const [roleCode, setRoleCode] = useState("receptionist");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const userQuery = useQuery({
    queryKey: ["admin", "users", userId],
    queryFn: () => getUserRequest(userId!),
    enabled: Boolean(userId),
  });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin", "users", userId] });
    await queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
  };

  const updateMutation = useMutation({
    mutationFn: (payload: { first_name?: string; last_name?: string; phone?: string }) =>
      updateUserRequest(userId!, payload),
    onSuccess: async () => {
      await invalidate();
      setSuccess("User updated.");
      setError(null);
    },
    onError: (err) => {
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to update user.");
    },
  });

  const assignMutation = useMutation({
    mutationFn: () => assignRoleRequest(userId!, { role_code: roleCode }),
    onSuccess: async () => {
      await invalidate();
      setSuccess("Role assigned.");
      setError(null);
    },
    onError: (err) => {
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to assign role.");
    },
  });

  const removeMutation = useMutation({
    mutationFn: (code: string) => removeRoleRequest(userId!, code),
    onSuccess: async () => {
      await invalidate();
      setSuccess("Role removed.");
      setError(null);
    },
    onError: (err) => {
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to remove role.");
    },
  });

  const disableMutation = useMutation({
    mutationFn: () => disableUserRequest(userId!),
    onSuccess: async () => {
      await invalidate();
      setSuccess("User disabled.");
      setError(null);
    },
    onError: (err) => {
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to disable user.");
    },
  });

  const user = userQuery.data;
  const isSelf = currentUser?.id === userId;

  function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) return;
    const form = new FormData(event.currentTarget);
    updateMutation.mutate({
      first_name: String(form.get("first_name") ?? "").trim(),
      last_name: String(form.get("last_name") ?? "").trim(),
      phone: String(form.get("phone") ?? "").trim() || undefined,
    });
  }

  if (userQuery.isLoading) {
    return <p className="text-sm text-muted">Loading user…</p>;
  }

  if (!user) {
    return (
      <div className="space-y-4">
        <p className={alertErrorClassName}>User not found.</p>
        <Link to="/admin/users" className="text-sm text-primary hover:underline">
          Back to users
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link to="/admin/users" className="text-sm text-primary hover:underline">
          ← Back to users
        </Link>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">
          {user.first_name} {user.last_name}
        </h2>
        <p className="mt-1 text-sm text-muted">{user.email}</p>
      </div>

      {error && <p className={alertErrorClassName}>{error}</p>}
      {success && <p className={alertSuccessClassName}>{success}</p>}

      <div className="rounded-lg border border-border bg-white p-6 text-sm">
        <dl className="grid gap-3 sm:grid-cols-2">
          <div>
            <dt className="text-muted">Status</dt>
            <dd className="font-medium capitalize">{user.status}</dd>
          </div>
          <div>
            <dt className="text-muted">Last login</dt>
            <dd className="font-medium">
              {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Never"}
            </dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-muted">Roles</dt>
            <dd className="mt-1 flex flex-wrap gap-2">
              {user.roles.length === 0 && <span>—</span>}
              {user.roles.map((role) => (
                <span
                  key={role}
                  className="inline-flex items-center gap-2 rounded-full bg-surface px-3 py-1 text-xs font-medium"
                >
                  {role}
                  <PermissionGuard permission="admin:users">
                    <button
                      type="button"
                      disabled={removeMutation.isPending}
                      onClick={() => removeMutation.mutate(role)}
                      className="text-error hover:underline"
                      aria-label={`Remove ${role}`}
                    >
                      ×
                    </button>
                  </PermissionGuard>
                </span>
              ))}
            </dd>
          </div>
        </dl>
      </div>

      <form className="space-y-4 rounded-lg border border-border bg-white p-6" onSubmit={handleProfileSubmit}>
        <h3 className="text-lg font-medium text-slate-900">Profile</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className={labelClassName}>
            <span className={labelTextClassName}>First name</span>
            <input
              name="first_name"
              className={inputClassName}
              defaultValue={user.first_name}
              required
            />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>Last name</span>
            <input name="last_name" className={inputClassName} defaultValue={user.last_name} required />
          </label>
        </div>
        <label className={labelClassName}>
          <span className={labelTextClassName}>Phone</span>
          <input name="phone" className={inputClassName} defaultValue={user.phone ?? ""} />
        </label>
        <button type="submit" disabled={updateMutation.isPending} className={primaryButtonClassName}>
          {updateMutation.isPending ? "Saving…" : "Save profile"}
        </button>
      </form>

      <PermissionGuard permission="admin:users">
        <div className="space-y-4 rounded-lg border border-border bg-white p-6">
          <h3 className="text-lg font-medium text-slate-900">Assign role</h3>
          <div className="flex flex-wrap gap-2">
            <select
              className={inputClassName}
              value={roleCode}
              onChange={(e) => setRoleCode(e.target.value)}
            >
              {TENANT_ROLE_OPTIONS.filter((role) => !user.roles.includes(role.code)).map((role) => (
                <option key={role.code} value={role.code}>
                  {role.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={assignMutation.isPending || user.roles.includes(roleCode)}
              onClick={() => assignMutation.mutate()}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 disabled:opacity-60"
            >
              {assignMutation.isPending ? "Assigning…" : "Assign role"}
            </button>
          </div>
        </div>

        {!isSelf && user.status === "active" && (
          <button
            type="button"
            disabled={disableMutation.isPending}
            onClick={() => {
              if (window.confirm(`Disable ${user.email}?`)) {
                disableMutation.mutate();
              }
            }}
            className="rounded-lg border border-error/30 bg-red-50 px-4 py-2 text-sm font-medium text-error hover:bg-red-100 disabled:opacity-60"
          >
            {disableMutation.isPending ? "Disabling…" : "Disable user"}
          </button>
        )}
      </PermissionGuard>
    </div>
  );
}
