import { FormEvent, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  assignRoleRequest,
  disableUserRequest,
  getUserRequest,
  removeRoleRequest,
  updateUserRequest,
} from "@/api/endpoints/admin-users";
import { ApiError } from "@/api/errors";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import { AdminPageFrame } from "@/components/enterprise";
import { Button, FieldLabel, Input, Modal, Select, useToast } from "@/components/ui";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { GlassCard } from "@/components/ui/GlassCard";
import { TENANT_ROLE_OPTIONS } from "@/lib/admin-constants";
import { useAuth } from "@/providers/AuthProvider";

export function UserDetailPage() {
  const { userId } = useParams<{ userId: string }>();
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [roleCode, setRoleCode] = useState("receptionist");
  const [disableOpen, setDisableOpen] = useState(false);

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
      toast.success("User updated.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to update user.");
    },
  });

  const assignMutation = useMutation({
    mutationFn: () => assignRoleRequest(userId!, { role_code: roleCode }),
    onSuccess: async () => {
      await invalidate();
      toast.success("Role assigned.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to assign role.");
    },
  });

  const removeMutation = useMutation({
    mutationFn: (code: string) => removeRoleRequest(userId!, code),
    onSuccess: async () => {
      await invalidate();
      toast.success("Role removed.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to remove role.");
    },
  });

  const disableMutation = useMutation({
    mutationFn: () => disableUserRequest(userId!),
    onSuccess: async () => {
      await invalidate();
      setDisableOpen(false);
      toast.success("User disabled.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to disable user.");
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
      <AdminPageFrame title="User not found" description="The requested account could not be loaded.">
        <Alert variant="error">User not found.</Alert>
      </AdminPageFrame>
    );
  }

  return (
    <AdminPageFrame title={`${user.first_name} ${user.last_name}`} description={user.email}>
      <div className="grid gap-6 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-4">
          <GlassCard strong className="text-sm">
            <h3 className="text-base font-semibold text-foreground">Account summary</h3>
            <dl className="mt-4 grid gap-4">
              <div>
                <dt className="text-muted">Status</dt>
                <dd className="mt-1">
                  <Badge variant={user.status === "active" ? "success" : "neutral"} className="capitalize">
                    {user.status}
                  </Badge>
                </dd>
              </div>
              <div>
                <dt className="text-muted">Last login</dt>
                <dd className="mt-1 font-medium text-foreground">
                  {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Never"}
                </dd>
              </div>
              <div>
                <dt className="text-muted">Roles</dt>
                <dd className="mt-2 flex flex-wrap gap-2">
                  {user.roles.length === 0 && <span className="text-muted">—</span>}
                  {user.roles.map((role) => (
                    <Badge key={role} className="gap-2">
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
                    </Badge>
                  ))}
                </dd>
              </div>
            </dl>
          </GlassCard>

          <PermissionGuard permission="admin:users">
            <GlassCard strong className="space-y-4">
              <h3 className="text-base font-semibold text-foreground">Assign role</h3>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Select value={roleCode} onChange={(e) => setRoleCode(e.target.value)}>
                  {TENANT_ROLE_OPTIONS.filter((role) => !user.roles.includes(role.code)).map((role) => (
                    <option key={role.code} value={role.code}>
                      {role.label}
                    </option>
                  ))}
                </Select>
                <Button
                  type="button"
                  disabled={assignMutation.isPending || user.roles.includes(roleCode)}
                  onClick={() => assignMutation.mutate()}
                >
                  {assignMutation.isPending ? "Assigning…" : "Assign"}
                </Button>
              </div>
            </GlassCard>

            {!isSelf && user.status === "active" && (
              <>
                <Button type="button" variant="danger" onClick={() => setDisableOpen(true)}>
                  Disable user account
                </Button>
                <Modal
                  open={disableOpen}
                  title="Disable user"
                  onClose={() => setDisableOpen(false)}
                  footer={
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="secondary" onClick={() => setDisableOpen(false)}>
                        Cancel
                      </Button>
                      <Button
                        type="button"
                        variant="danger"
                        disabled={disableMutation.isPending}
                        onClick={() => disableMutation.mutate()}
                      >
                        {disableMutation.isPending ? "Disabling…" : "Confirm disable"}
                      </Button>
                    </div>
                  }
                >
                  <p className="text-sm text-muted">
                    Disable <strong>{user.email}</strong>? They will no longer be able to sign in.
                  </p>
                </Modal>
              </>
            )}
          </PermissionGuard>
        </div>

        <div className="lg:col-span-8">
          <form className="glass-panel-strong space-y-6 p-6 sm:p-8" onSubmit={handleProfileSubmit}>
            <div>
              <h3 className="text-base font-semibold text-foreground">Profile details</h3>
              <p className="mt-1 text-sm text-muted">Update the user&apos;s display name and contact phone.</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <FieldLabel htmlFor="first_name" label="First name">
                <Input name="first_name" id="first_name" defaultValue={user.first_name} required />
              </FieldLabel>
              <FieldLabel htmlFor="last_name" label="Last name">
                <Input name="last_name" id="last_name" defaultValue={user.last_name} required />
              </FieldLabel>
            </div>
            <FieldLabel htmlFor="phone" label="Phone">
              <Input name="phone" id="phone" defaultValue={user.phone ?? ""} />
            </FieldLabel>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving…" : "Save profile"}
            </Button>
          </form>
        </div>
      </div>
    </AdminPageFrame>
  );
}
