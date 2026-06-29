import { zodResolver } from "@hookform/resolvers/zod";
import { FormEvent, useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { UserPlus, Users } from "lucide-react";
import { inviteUserRequest, searchUsersRequest } from "@/api/endpoints/admin-users";
import { ApiError } from "@/api/errors";
import {
  AdminPageFrame,
  DataGridShell,
  DataToolbar,
  EmptyState,
  PaginationBar,
} from "@/components/enterprise";
import { FormField } from "@/components/forms/FormField";
import { Badge } from "@/components/ui/Badge";
import { Button, Modal, useToast } from "@/components/ui";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableLoading,
  TableRow,
} from "@/components/ui/Table";
import { TENANT_ROLE_OPTIONS } from "@/lib/admin-constants";

const inviteUserSchema = z.object({
  first_name: z.string().trim().min(1, "First name is required"),
  last_name: z.string().trim().min(1, "Last name is required"),
  email: z.string().trim().email("Enter a valid email"),
  role_code: z.string().min(1, "Role is required"),
});

type InviteUserForm = z.infer<typeof inviteUserSchema>;
const PAGE_SIZE = 20;

function userStatusVariant(status: string): "success" | "warning" | "error" | "neutral" {
  if (status === "active") return "success";
  if (status === "invited") return "warning";
  if (status === "disabled") return "error";
  return "neutral";
}

export function UsersPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteToken, setInviteToken] = useState<string | null>(null);

  const inviteForm = useForm<InviteUserForm>({
    resolver: zodResolver(inviteUserSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      role_code: "receptionist",
    },
  });

  const usersQuery = useQuery({
    queryKey: ["admin", "users", query, page],
    queryFn: () => searchUsersRequest({ q: query || undefined, page, page_size: PAGE_SIZE }),
  });

  const inviteMutation = useMutation({
    mutationFn: inviteUserRequest,
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      setInviteOpen(false);
      inviteForm.reset();
      setInviteToken(data.invite_token);
      toast.success(`Invitation sent to ${data.email}.`);
    },
    onError: (err) => {
      setInviteToken(null);
      toast.error(err instanceof ApiError ? err.message : "Failed to invite user.");
    },
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setQuery(search.trim());
    setPage(1);
  }

  function onInvite(values: InviteUserForm) {
    setInviteToken(null);
    inviteMutation.mutate({
      email: values.email.trim().toLowerCase(),
      first_name: values.first_name.trim(),
      last_name: values.last_name.trim(),
      role_codes: values.role_code ? [values.role_code] : [],
    });
  }

  const users = usersQuery.data?.data ?? [];
  const pagination = usersQuery.data?.pagination;

  return (
    <AdminPageFrame
      title="Users & access control"
      description="Invite hospital staff, assign roles, and manage tenant user accounts."
      actions={
        <Button type="button" onClick={() => setInviteOpen(true)}>
          <UserPlus className="mr-2 h-4 w-4" />
          Invite user
        </Button>
      }
    >
      {inviteToken && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-warning">
          Development invite token: <code className="font-mono text-xs">{inviteToken}</code>
        </p>
      )}

      <Modal
        open={inviteOpen}
        title="Invite hospital user"
        onClose={() => setInviteOpen(false)}
        footer={
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setInviteOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" form="invite-user-form" disabled={inviteMutation.isPending}>
              {inviteMutation.isPending ? "Sending invite…" : "Send invitation"}
            </Button>
          </div>
        }
      >
        <form id="invite-user-form" className="space-y-6" onSubmit={inviteForm.handleSubmit(onInvite)}>
          <p className="text-sm text-muted">
            The invited user will receive credentials to access modules based on their assigned role.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField name="first_name" control={inviteForm.control} label="First name" />
            <FormField name="last_name" control={inviteForm.control} label="Last name" />
            <FormField name="email" control={inviteForm.control} label="Work email" type="email" className="sm:col-span-2" />
            <FormField name="role_code" control={inviteForm.control} label="Role" as="select" className="sm:col-span-2">
              {TENANT_ROLE_OPTIONS.map((role) => (
                <option key={role.code} value={role.code}>
                  {role.label}
                </option>
              ))}
            </FormField>
          </div>
        </form>
      </Modal>

      <DataToolbar
        searchValue={search}
        onSearchChange={setSearch}
        onSearchSubmit={handleSearch}
        searchPlaceholder="Search by name or email"
      />

      <DataGridShell
        footer={
          pagination && pagination.total_items > 0 ? (
            <PaginationBar pagination={pagination} onPageChange={setPage} />
          ) : undefined
        }
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>User</TableHeaderCell>
              <TableHeaderCell>Email</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Roles</TableHeaderCell>
              <TableHeaderCell className="text-right">Actions</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {usersQuery.isLoading && <TableLoading colSpan={5}>Loading users…</TableLoading>}
            {!usersQuery.isLoading && users.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="p-0">
                  <EmptyState
                    icon={Users}
                    title="No users match your search"
                    description="Invite administrators, receptionists, and clinical staff to collaborate on this hospital tenant."
                    action={
                      <Button type="button" onClick={() => setInviteOpen(true)}>
                        Invite user
                      </Button>
                    }
                  />
                </TableCell>
              </TableRow>
            )}
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">
                  {user.first_name} {user.last_name}
                </TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <Badge variant={userStatusVariant(user.status)} className="capitalize">
                    {user.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {user.roles.length === 0 && "—"}
                    {user.roles.map((role) => (
                      <Badge key={role} variant="neutral">
                        {role}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <Link to={`/admin/users/${user.id}`}>
                    <Button type="button" variant="ghost" size="sm">
                      Manage
                    </Button>
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DataGridShell>
    </AdminPageFrame>
  );
}
