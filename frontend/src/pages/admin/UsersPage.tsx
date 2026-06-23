import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { inviteUserRequest, searchUsersRequest } from "@/api/endpoints/admin-users";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  alertSuccessClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";
import { TENANT_ROLE_OPTIONS } from "@/lib/admin-constants";

export function UsersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [showInvite, setShowInvite] = useState(false);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [roleCode, setRoleCode] = useState("receptionist");

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [inviteToken, setInviteToken] = useState<string | null>(null);

  const usersQuery = useQuery({
    queryKey: ["admin", "users", query],
    queryFn: () => searchUsersRequest({ q: query || undefined, page: 1, page_size: 50 }),
  });

  const inviteMutation = useMutation({
    mutationFn: inviteUserRequest,
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      setShowInvite(false);
      setFirstName("");
      setLastName("");
      setEmail("");
      setInviteToken(data.invite_token);
      setSuccess(`Invitation sent to ${data.email}.`);
      setError(null);
    },
    onError: (err) => {
      setInviteToken(null);
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to invite user.");
    },
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setQuery(search.trim());
  }

  function handleInvite(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setInviteToken(null);
    inviteMutation.mutate({
      email: email.trim().toLowerCase(),
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      role_codes: roleCode ? [roleCode] : [],
    });
  }

  const users = usersQuery.data?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Users</h2>
          <p className="mt-1 text-sm text-muted">Invite staff and manage tenant user accounts.</p>
        </div>
        <button
          type="button"
          onClick={() => setShowInvite((open) => !open)}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
        >
          {showInvite ? "Cancel invite" : "Invite user"}
        </button>
      </div>

      {error && <p className={alertErrorClassName}>{error}</p>}
      {success && <p className={alertSuccessClassName}>{success}</p>}
      {inviteToken && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Dev invite token: <code className="font-mono text-xs">{inviteToken}</code>
        </p>
      )}

      {showInvite && (
        <form className="grid gap-4 rounded-lg border border-border bg-white p-6 sm:grid-cols-2" onSubmit={handleInvite}>
          <h3 className="sm:col-span-2 text-lg font-medium text-slate-900">Invite user</h3>
          <label className={labelClassName}>
            <span className={labelTextClassName}>First name</span>
            <input className={inputClassName} value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>Last name</span>
            <input className={inputClassName} value={lastName} onChange={(e) => setLastName(e.target.value)} required />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>Email</span>
            <input
              type="email"
              className={inputClassName}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>Role</span>
            <select className={inputClassName} value={roleCode} onChange={(e) => setRoleCode(e.target.value)}>
              {TENANT_ROLE_OPTIONS.map((role) => (
                <option key={role.code} value={role.code}>
                  {role.label}
                </option>
              ))}
            </select>
          </label>
          <div className="sm:col-span-2">
            <button type="submit" disabled={inviteMutation.isPending} className={primaryButtonClassName}>
              {inviteMutation.isPending ? "Sending invite…" : "Send invitation"}
            </button>
          </div>
        </form>
      )}

      <form className="flex gap-2" onSubmit={handleSearch}>
        <input
          className={inputClassName}
          placeholder="Search by name or email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button
          type="submit"
          className="shrink-0 rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-surface"
        >
          Search
        </button>
      </form>

      <div className="overflow-hidden rounded-lg border border-border bg-white">
        <table className="min-w-full text-sm">
          <thead className="border-b border-border bg-surface/60 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Roles</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {usersQuery.isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-muted">
                  Loading users…
                </td>
              </tr>
            )}
            {users.map((user) => (
              <tr key={user.id} className="border-b border-border last:border-0">
                <td className="px-4 py-3">
                  {user.first_name} {user.last_name}
                </td>
                <td className="px-4 py-3">{user.email}</td>
                <td className="px-4 py-3 capitalize">{user.status}</td>
                <td className="px-4 py-3">{user.roles.join(", ") || "—"}</td>
                <td className="px-4 py-3 text-right">
                  <Link to={`/admin/users/${user.id}`} className="text-primary hover:underline">
                    View
                  </Link>
                </td>
              </tr>
            ))}
            {!usersQuery.isLoading && users.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-muted">
                  No users found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
