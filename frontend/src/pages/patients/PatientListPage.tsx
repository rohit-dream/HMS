import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { UserPlus, Users } from "lucide-react";
import {
  AdminPageFrame,
  DataGridShell,
  DataToolbar,
  EmptyState,
  PaginationBar,
} from "@/components/enterprise";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import { Alert, Badge, Button, primaryLinkClassName } from "@/components/ui";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableLoading,
  TableRow,
} from "@/components/ui/Table";
import { usePatientList } from "@/features/patients/hooks/usePatientList";
import {
  calculateAge,
  formatDate,
  formatPatientName,
  formatPhone,
  genderLabel,
} from "@/lib/formatters";

const PAGE_SIZE = 20;

export function PatientListPage() {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [searchHint, setSearchHint] = useState<string | null>(null);

  const patientsQuery = usePatientList({
    search: query,
    page,
    pageSize: PAGE_SIZE,
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    const trimmed = search.trim();
    if (trimmed.length > 0 && trimmed.length < 2) {
      setSearchHint("Enter at least 2 characters to search by name, phone, MRN, or email.");
      return;
    }
    setSearchHint(null);
    setQuery(trimmed);
    setPage(1);
  }

  const patients = patientsQuery.data?.data ?? [];
  const pagination = patientsQuery.data?.pagination;

  return (
    <AdminPageFrame
      title="Patients"
      description="Search and browse registered patients by name, phone, medical record number, or email."
      actions={
        <PermissionGuard permission="patient:create">
          <Link to="/patients/new" className={primaryLinkClassName}>
            <UserPlus className="mr-2 h-4 w-4" />
            Register patient
          </Link>
        </PermissionGuard>
      }
    >
      <DataToolbar
        searchValue={search}
        onSearchChange={(value) => {
          setSearch(value);
          if (searchHint) setSearchHint(null);
        }}
        onSearchSubmit={handleSearch}
        searchPlaceholder="Search name, phone, MRN, or email"
      />

      {searchHint && <Alert variant="warning">{searchHint}</Alert>}

      {patientsQuery.isError && (
        <Alert variant="error">
          {patientsQuery.error instanceof Error
            ? patientsQuery.error.message
            : "Unable to load patients. Please try again."}
        </Alert>
      )}

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
              <TableHeaderCell>Patient</TableHeaderCell>
              <TableHeaderCell>MRN</TableHeaderCell>
              <TableHeaderCell>Phone</TableHeaderCell>
              <TableHeaderCell>Age / DOB</TableHeaderCell>
              <TableHeaderCell>Gender</TableHeaderCell>
              <TableHeaderCell>Blood group</TableHeaderCell>
              <TableHeaderCell>Last visit</TableHeaderCell>
              <TableHeaderCell className="text-right">Actions</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {patientsQuery.isLoading && (
              <TableLoading colSpan={8}>Loading patient directory…</TableLoading>
            )}
            {!patientsQuery.isLoading && patients.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="p-0">
                  <EmptyState
                    icon={Users}
                    title={query ? "No patients match your search" : "No patients registered yet"}
                    description={
                      query
                        ? "Try a different name, phone number, or MRN."
                        : "Register your first patient to start building the hospital patient registry."
                    }
                    action={
                      <PermissionGuard permission="patient:create">
                        <Link to="/patients/new" className={primaryLinkClassName}>
                          Register patient
                        </Link>
                      </PermissionGuard>
                    }
                  />
                </TableCell>
              </TableRow>
            )}
            {patients.map((patient) => (
              <TableRow key={patient.id}>
                <TableCell>
                  <div className="font-medium text-foreground">
                    {formatPatientName(patient.first_name, patient.last_name)}
                  </div>
                  {patient.email && (
                    <div className="mt-0.5 text-xs text-muted">{patient.email}</div>
                  )}
                </TableCell>
                <TableCell className="font-mono text-xs">{patient.mrn}</TableCell>
                <TableCell>{formatPhone(patient.phone)}</TableCell>
                <TableCell>
                  <div>{calculateAge(patient.date_of_birth)} yrs</div>
                  <div className="text-xs text-muted">{formatDate(patient.date_of_birth)}</div>
                </TableCell>
                <TableCell>
                  <Badge variant="neutral" className="capitalize">
                    {genderLabel(patient.gender)}
                  </Badge>
                </TableCell>
                <TableCell>{patient.blood_group ?? "—"}</TableCell>
                <TableCell>{formatDate(patient.last_visit_date)}</TableCell>
                <TableCell className="text-right">
                  <Link to={`/patients/${patient.id}`}>
                    <Button type="button" variant="ghost" size="sm">
                      View profile
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
