import { Link } from "react-router-dom";
import { CalendarDays, ExternalLink } from "lucide-react";
import type { PatientVisitHistoryItem } from "@/api/types/patients";
import type { PaginationMeta } from "@/api/types";
import { EmptyState, PaginationBar } from "@/components/enterprise";
import { Badge } from "@/components/ui";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableLoading,
  TableRow,
} from "@/components/ui/Table";
import { OpdVisitStatusBadge } from "@/features/opd/components/OpdVisitStatusBadge";
import {
  isOpdVisitStatus,
  patientVisitStatusLabel,
  truncateText,
} from "@/features/patients/utils/visitHistoryFormatters";
import { formatDate } from "@/lib/formatters";

interface PatientVisitHistoryTableProps {
  visits: PatientVisitHistoryItem[];
  isLoading: boolean;
  pagination?: PaginationMeta;
  onPageChange?: (page: number) => void;
  errorMessage?: string | null;
}

export function PatientVisitHistoryTable({
  visits,
  isLoading,
  pagination,
  onPageChange,
  errorMessage,
}: PatientVisitHistoryTableProps) {
  return (
    <div className="space-y-4">
      {errorMessage && (
        <p className="text-sm text-error" role="alert">
          {errorMessage}
        </p>
      )}

      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Date</TableHeaderCell>
            <TableHeaderCell>Reference</TableHeaderCell>
            <TableHeaderCell>Doctor</TableHeaderCell>
            <TableHeaderCell>Chief complaint</TableHeaderCell>
            <TableHeaderCell>Diagnosis</TableHeaderCell>
            <TableHeaderCell>Department</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            <TableHeaderCell className="text-right">Summary</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading && (
            <TableLoading colSpan={8}>Loading visit history…</TableLoading>
          )}
          {!isLoading && visits.length === 0 && (
            <TableRow>
              <TableCell colSpan={8} className="p-0">
                <EmptyState
                  icon={CalendarDays}
                  title="No visits yet"
                  description="Completed OPD consultations will appear here chronologically."
                />
              </TableCell>
            </TableRow>
          )}
          {visits.map((visit) => (
            <TableRow key={visit.id}>
              <TableCell className="whitespace-nowrap">{formatDate(visit.visit_date)}</TableCell>
              <TableCell className="font-mono text-xs">{visit.reference_number}</TableCell>
              <TableCell>{visit.doctor_name}</TableCell>
              <TableCell className="max-w-[12rem] truncate" title={visit.chief_complaint ?? undefined}>
                {truncateText(visit.chief_complaint, 60)}
              </TableCell>
              <TableCell className="max-w-[12rem] truncate" title={visit.diagnosis ?? undefined}>
                {truncateText(visit.diagnosis, 60)}
              </TableCell>
              <TableCell>{visit.department_name ?? "—"}</TableCell>
              <TableCell>
                {isOpdVisitStatus(visit.status) ? (
                  <OpdVisitStatusBadge status={visit.status} />
                ) : (
                  <Badge variant="neutral" className="capitalize">
                    {patientVisitStatusLabel(visit.status)}
                  </Badge>
                )}
              </TableCell>
              <TableCell className="text-right">
                <Link
                  to={`/opd/visits/${visit.id}`}
                  className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                >
                  View
                  <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {pagination && pagination.total_items > 0 && onPageChange && (
        <PaginationBar pagination={pagination} onPageChange={onPageChange} />
      )}
    </div>
  );
}
