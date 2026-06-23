import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listStaffRequest } from "@/api/endpoints/staff";
import {
  Button,
  Input,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableEmpty,
  TableHead,
  TableHeaderCell,
  TableLoading,
  TableRow,
} from "@/components/ui";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "on_leave", label: "On leave" },
  { value: "terminated", label: "Terminated" },
];

export function StaffPage() {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");

  const staffQuery = useQuery({
    queryKey: ["admin", "staff", query, status],
    queryFn: () =>
      listStaffRequest({
        search: query || undefined,
        status: status || undefined,
        page: 1,
        page_size: 100,
      }),
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setQuery(search.trim());
  }

  const staff = staffQuery.data?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Staff</h2>
          <p className="mt-1 text-sm text-muted">
            Manage hospital employees, departments, and employment status.
          </p>
        </div>
        <Link
          to="/admin/staff/new"
          className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
        >
          Add staff member
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        <form className="flex min-w-[16rem] flex-1 gap-2" onSubmit={handleSearch}>
          <Input
            placeholder="Search name, email, or employee code"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button type="submit" variant="secondary" className="shrink-0">
            Search
          </Button>
        </form>
        <Select
          className="w-40"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          aria-label="Filter by status"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value || "all"} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Code</TableHeaderCell>
              <TableHeaderCell>Name</TableHeaderCell>
              <TableHeaderCell>Department</TableHeaderCell>
              <TableHeaderCell>Designation</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {staffQuery.isLoading && <TableLoading colSpan={6}>Loading staff…</TableLoading>}
            {staff.map((member) => (
              <TableRow key={member.id}>
                <TableCell className="font-mono text-xs">{member.employee_code}</TableCell>
                <TableCell>
                  {member.first_name} {member.last_name}
                  {member.is_doctor && (
                    <span className="ml-2 rounded bg-primary/10 px-2 py-0.5 text-xs text-primary">
                      Doctor
                    </span>
                  )}
                </TableCell>
                <TableCell>{member.department_name ?? "—"}</TableCell>
                <TableCell>{member.designation ?? "—"}</TableCell>
                <TableCell className="capitalize">{member.status.replace("_", " ")}</TableCell>
                <TableCell className="text-right">
                  <Link
                    to={`/admin/staff/${member.id}`}
                    className="text-sm text-primary hover:underline"
                  >
                    Edit
                  </Link>
                </TableCell>
              </TableRow>
            ))}
            {!staffQuery.isLoading && staff.length === 0 && (
              <TableEmpty colSpan={6}>No staff members found.</TableEmpty>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
