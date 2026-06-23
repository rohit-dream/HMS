import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listDoctorsRequest } from "@/api/endpoints/doctors";
import {
  Button,
  Input,
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

export function DoctorsPage() {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");

  const doctorsQuery = useQuery({
    queryKey: ["admin", "doctors", query],
    queryFn: () => listDoctorsRequest({ search: query || undefined, page: 1, page_size: 100 }),
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setQuery(search.trim());
  }

  const doctors = doctorsQuery.data?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Doctors</h2>
          <p className="mt-1 text-sm text-muted">
            Manage doctor profiles, fees, and weekly availability schedules.
          </p>
        </div>
        <Link
          to="/admin/doctors/new"
          className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
        >
          Add doctor
        </Link>
      </div>

      <form className="flex gap-2" onSubmit={handleSearch}>
        <Input
          placeholder="Search name, specialization, or registration no."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Button type="submit" variant="secondary" className="shrink-0">
          Search
        </Button>
      </form>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Name</TableHeaderCell>
              <TableHeaderCell>Specialization</TableHeaderCell>
              <TableHeaderCell>Department</TableHeaderCell>
              <TableHeaderCell>Consultation fee</TableHeaderCell>
              <TableHeaderCell>Available</TableHeaderCell>
              <TableHeaderCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {doctorsQuery.isLoading && <TableLoading colSpan={6}>Loading doctors…</TableLoading>}
            {doctors.map((doctor) => (
              <TableRow key={doctor.id}>
                <TableCell>
                  <div>
                    {doctor.first_name} {doctor.last_name}
                  </div>
                  <div className="font-mono text-xs text-muted">{doctor.employee_code}</div>
                </TableCell>
                <TableCell>{doctor.specialization}</TableCell>
                <TableCell>{doctor.department_name ?? "—"}</TableCell>
                <TableCell>{doctor.consultation_fee}</TableCell>
                <TableCell>{doctor.is_available ? "Yes" : "No"}</TableCell>
                <TableCell className="space-x-3 text-right">
                  <Link
                    to={`/admin/doctors/${doctor.id}`}
                    className="text-sm text-primary hover:underline"
                  >
                    Edit
                  </Link>
                  <Link
                    to={`/admin/doctors/${doctor.id}/schedule`}
                    className="text-sm text-primary hover:underline"
                  >
                    Schedule
                  </Link>
                </TableCell>
              </TableRow>
            ))}
            {!doctorsQuery.isLoading && doctors.length === 0 && (
              <TableEmpty colSpan={6}>No doctors found.</TableEmpty>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
