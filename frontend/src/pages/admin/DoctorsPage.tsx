import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Stethoscope, UserRound } from "lucide-react";
import { listDoctorsRequest } from "@/api/endpoints/doctors";
import {
  AdminPageFrame,
  DataGridShell,
  DataToolbar,
  EmptyState,
  PaginationBar,
} from "@/components/enterprise";
import { Badge } from "@/components/ui/Badge";
import { Button, primaryLinkClassName } from "@/components/ui";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableLoading,
  TableRow,
} from "@/components/ui/Table";

const PAGE_SIZE = 20;

export function DoctorsPage() {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  const doctorsQuery = useQuery({
    queryKey: ["admin", "doctors", query, page],
    queryFn: () => listDoctorsRequest({ search: query || undefined, page, page_size: PAGE_SIZE }),
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setQuery(search.trim());
    setPage(1);
  }

  const doctors = doctorsQuery.data?.data ?? [];
  const pagination = doctorsQuery.data?.pagination;

  return (
    <AdminPageFrame
      title="Doctor registry"
      description="Manage physician profiles, consultation fees, availability, and weekly schedules."
      actions={
        <Link to="/admin/doctors/new" className={primaryLinkClassName}>
          <UserRound className="mr-2 h-4 w-4" />
          Add doctor
        </Link>
      }
    >
      <DataToolbar
        searchValue={search}
        onSearchChange={setSearch}
        onSearchSubmit={handleSearch}
        searchPlaceholder="Search name, specialization, or registration number"
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
              <TableHeaderCell>Physician</TableHeaderCell>
              <TableHeaderCell>Specialization</TableHeaderCell>
              <TableHeaderCell>Department</TableHeaderCell>
              <TableHeaderCell>Consultation fee</TableHeaderCell>
              <TableHeaderCell>Availability</TableHeaderCell>
              <TableHeaderCell className="text-right">Actions</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {doctorsQuery.isLoading && <TableLoading colSpan={6}>Loading doctor registry…</TableLoading>}
            {!doctorsQuery.isLoading && doctors.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="p-0">
                  <EmptyState
                    icon={Stethoscope}
                    title="No doctors registered"
                    description="Create doctor profiles linked to staff members and configure schedules for OPD readiness."
                    action={
                      <Link to="/admin/doctors/new" className={primaryLinkClassName}>
                        Add doctor
                      </Link>
                    }
                  />
                </TableCell>
              </TableRow>
            )}
            {doctors.map((doctor) => (
              <TableRow key={doctor.id}>
                <TableCell>
                  <div className="font-medium text-foreground">
                    {doctor.first_name} {doctor.last_name}
                  </div>
                  <div className="font-mono text-xs text-muted">{doctor.employee_code}</div>
                </TableCell>
                <TableCell>{doctor.specialization}</TableCell>
                <TableCell>{doctor.department_name ?? "—"}</TableCell>
                <TableCell>{doctor.consultation_fee}</TableCell>
                <TableCell>
                  <Badge variant={doctor.is_available ? "success" : "neutral"}>
                    {doctor.is_available ? "Available" : "Unavailable"}
                  </Badge>
                </TableCell>
                <TableCell className="space-x-2 text-right">
                  <Link to={`/admin/doctors/${doctor.id}`}>
                    <Button type="button" variant="ghost" size="sm">
                      Profile
                    </Button>
                  </Link>
                  <Link to={`/admin/doctors/${doctor.id}/schedule`}>
                    <Button type="button" variant="secondary" size="sm">
                      Schedule
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
