import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { UserPlus, Users } from "lucide-react";
import { listStaffRequest } from "@/api/endpoints/staff";
import {
  AdminPageFrame,
  DataGridShell,
  DataToolbar,
  EmptyState,
  PaginationBar,
} from "@/components/enterprise";
import { Badge } from "@/components/ui/Badge";
import { Button, primaryLinkClassName, Select } from "@/components/ui";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableLoading,
  TableRow,
} from "@/components/ui/Table";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "on_leave", label: "On leave" },
  { value: "terminated", label: "Terminated" },
];

const PAGE_SIZE = 20;

function statusVariant(status: string): "success" | "warning" | "error" | "neutral" {
  if (status === "active") return "success";
  if (status === "on_leave") return "warning";
  if (status === "terminated") return "error";
  return "neutral";
}

export function StaffPage() {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const staffQuery = useQuery({
    queryKey: ["admin", "staff", query, status, page],
    queryFn: () =>
      listStaffRequest({
        search: query || undefined,
        status: status || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setQuery(search.trim());
    setPage(1);
  }

  const staff = staffQuery.data?.data ?? [];
  const pagination = staffQuery.data?.pagination;

  return (
    <AdminPageFrame
      title="Staff directory"
      description="Manage hospital employees, departments, designations, and employment lifecycle."
      actions={
        <Link to="/admin/staff/new" className={primaryLinkClassName}>
          <UserPlus className="mr-2 h-4 w-4" />
          Add staff member
        </Link>
      }
    >
      <DataToolbar
        searchValue={search}
        onSearchChange={setSearch}
        onSearchSubmit={handleSearch}
        searchPlaceholder="Search name, email, or employee code"
        filters={
          <Select
            className="w-44"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
            aria-label="Filter by status"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        }
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
              <TableHeaderCell>Employee</TableHeaderCell>
              <TableHeaderCell>Code</TableHeaderCell>
              <TableHeaderCell>Department</TableHeaderCell>
              <TableHeaderCell>Designation</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell className="text-right">Actions</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {staffQuery.isLoading && <TableLoading colSpan={6}>Loading staff directory…</TableLoading>}
            {!staffQuery.isLoading && staff.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="p-0">
                  <EmptyState
                    icon={Users}
                    title="No staff members found"
                    description="Adjust your search filters or add your first employee to build the hospital roster."
                    action={
                      <Link to="/admin/staff/new" className={primaryLinkClassName}>
                        Add staff member
                      </Link>
                    }
                  />
                </TableCell>
              </TableRow>
            )}
            {staff.map((member) => (
              <TableRow key={member.id}>
                <TableCell>
                  <div className="font-medium text-foreground">
                    {member.first_name} {member.last_name}
                  </div>
                  {member.is_doctor && (
                    <Badge variant="info" className="mt-1">
                      Doctor profile
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="font-mono text-xs">{member.employee_code}</TableCell>
                <TableCell>{member.department_name ?? "—"}</TableCell>
                <TableCell>{member.designation ?? "—"}</TableCell>
                <TableCell>
                  <Badge variant={statusVariant(member.status)} className="capitalize">
                    {member.status.replace("_", " ")}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Link to={`/admin/staff/${member.id}`}>
                    <Button type="button" variant="ghost" size="sm">
                      View / Edit
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
