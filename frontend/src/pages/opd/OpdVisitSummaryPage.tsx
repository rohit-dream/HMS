import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Stethoscope, UserRound } from "lucide-react";
import { ApiError } from "@/api/errors";
import { AdminPageFrame, FormPageLayout } from "@/components/enterprise";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import { Alert, Button, primaryLinkClassName } from "@/components/ui";
import { GlassCard } from "@/components/ui/GlassCard";
import { OpdConsultationWorkspace } from "@/features/opd/components/OpdConsultationWorkspace";
import { OpdVisitStatusBadge } from "@/features/opd/components/OpdVisitStatusBadge";
import {
  useOpdNotes,
  useOpdPrescriptions,
  useOpdVitals,
} from "@/features/opd/hooks/useOpdConsultation";
import { useOpdVisit } from "@/features/opd/hooks/useOpdVisit";
import { usePatient } from "@/features/patients/hooks/usePatient";
import { usePermissions } from "@/hooks/usePermissions";
import { formatDate, formatDateTime, formatPatientName } from "@/lib/formatters";

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-muted">{label}</dt>
      <dd className="mt-1 font-medium text-foreground">{value}</dd>
    </div>
  );
}

export function OpdVisitSummaryPage() {
  const { visitId } = useParams<{ visitId: string }>();
  const navigate = useNavigate();
  const { hasPermission } = usePermissions();
  const canConsult = hasPermission("opd:consult");

  const visitQuery = useOpdVisit(visitId);
  const visit = visitQuery.data;
  const patientQuery = usePatient(visit?.patient_id);
  const vitalsQuery = useOpdVitals(visitId);
  const notesQuery = useOpdNotes(visitId);
  const prescriptionsQuery = useOpdPrescriptions(visitId);

  const canOpenConsult =
    canConsult &&
    visit &&
    (visit.status === "waiting" || visit.status === "in_consultation");

  if (visitQuery.isLoading) {
    return (
      <AdminPageFrame title="OPD visit summary" description="Loading visit…">
        <div className="h-48 animate-pulse rounded-xl bg-surface-secondary" />
      </AdminPageFrame>
    );
  }

  if (visitQuery.error || !visit) {
    return (
      <AdminPageFrame title="OPD visit summary" description="Visit not found">
        <Alert variant="error">
          {visitQuery.error instanceof ApiError
            ? visitQuery.error.message
            : "Unable to load this OPD visit."}
        </Alert>
        <Link to="/patients" className={`${primaryLinkClassName} mt-4 inline-flex`}>
          Back to patients
        </Link>
      </AdminPageFrame>
    );
  }

  const patient = patientQuery.data;
  const patientName =
    patient != null
      ? formatPatientName(patient.first_name, patient.last_name)
      : (visit.patient_name ?? "Patient");

  return (
    <AdminPageFrame
      title={`Visit ${visit.visit_number}`}
      description={`${patientName}${visit.patient_mrn ? ` · ${visit.patient_mrn}` : ""} · ${formatDate(visit.visit_date)}`}
      actions={
        <div className="flex flex-wrap items-center gap-2">
          {patient && (
            <Link
              to={`/patients/${patient.id}`}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground transition-all duration-200 hover:bg-hover"
            >
              <UserRound className="h-4 w-4" />
              Patient profile
            </Link>
          )}
          {canOpenConsult && (
            <PermissionGuard permission="opd:consult">
              <Link to={`/opd/consult/${visit.id}`} className={primaryLinkClassName}>
                <Stethoscope className="mr-2 inline h-4 w-4" />
                {visit.status === "in_consultation" ? "Continue consultation" : "Open consultation"}
              </Link>
            </PermissionGuard>
          )}
          <Button variant="outline" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </div>
      }
    >
      <div className="mb-6 flex flex-wrap items-center gap-3 text-sm">
        <OpdVisitStatusBadge status={visit.status} />
        <span className="text-muted">
          Doctor: {visit.doctor_name ?? "—"}
          {visit.location_name ? ` · ${visit.location_name}` : ""}
        </span>
        {visit.token_number != null && (
          <span className="text-muted">Token #{visit.token_number}</span>
        )}
      </div>

      <FormPageLayout
        sidebar={
          <GlassCard strong padding="md" className="text-sm">
            <h3 className="text-base font-semibold text-foreground">Visit details</h3>
            <dl className="mt-4 grid gap-4">
              <DetailRow label="Visit type" value={visit.visit_type === "walk_in" ? "Walk-in" : "Appointment"} />
              <DetailRow label="Started" value={visit.started_at ? formatDateTime(visit.started_at) : "—"} />
              <DetailRow
                label="Completed"
                value={visit.completed_at ? formatDateTime(visit.completed_at) : "—"}
              />
              <DetailRow label="Vitals recorded" value={String(visit.vitals_count)} />
              <DetailRow label="Clinical notes" value={String(visit.notes_count)} />
              <DetailRow label="Prescriptions" value={String(visit.prescriptions_count)} />
            </dl>
          </GlassCard>
        }
      >
        <OpdConsultationWorkspace
          chiefComplaint={visit.chief_complaint}
          readOnly
          vitals={vitalsQuery.data ?? []}
          notes={notesQuery.data ?? []}
          prescriptions={prescriptionsQuery.data ?? []}
          allergies={patient?.allergies ?? []}
          onSaveVitals={async () => {}}
          onSaveNotes={async () => {}}
          onSavePrescription={async () => {}}
          isSaving={false}
        />
      </FormPageLayout>
    </AdminPageFrame>
  );
}
