import { useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, PlayCircle } from "lucide-react";
import { ApiError } from "@/api/errors";
import type { OpdNoteType } from "@/api/types/opd";
import { AdminPageFrame, FormPageLayout } from "@/components/enterprise";
import { Alert, Button, useToast } from "@/components/ui";
import { OpdConsultPatientPanel } from "@/features/opd/components/OpdConsultPatientPanel";
import { OpdConsultationWorkspace } from "@/features/opd/components/OpdConsultationWorkspace";
import { OpdVisitStatusBadge } from "@/features/opd/components/OpdVisitStatusBadge";
import { clearConsultationDraft } from "@/features/opd/hooks/useConsultationDraft";
import {
  useOpdConsultationActions,
  useOpdNotes,
  useOpdPrescriptions,
  useOpdVitals,
} from "@/features/opd/hooks/useOpdConsultation";
import { useOpdVisit } from "@/features/opd/hooks/useOpdVisit";
import { usePatient } from "@/features/patients/hooks/usePatient";
import { usePatientVisits } from "@/features/patients/hooks/usePatientVisits";
import { usePermissions } from "@/hooks/usePermissions";
import { formatDate } from "@/lib/formatters";

export function OpdConsultationPage() {
  const { visitId } = useParams<{ visitId: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const { hasPermission } = usePermissions();
  const canConsult = hasPermission("opd:consult");
  const canPrescribe = hasPermission("opd:prescribe");

  const visitQuery = useOpdVisit(visitId);
  const visit = visitQuery.data;
  const patientQuery = usePatient(visit?.patient_id);
  const visitsQuery = usePatientVisits(visit?.patient_id, 1, 5);
  const vitalsQuery = useOpdVitals(visitId);
  const notesQuery = useOpdNotes(visitId);
  const prescriptionsQuery = useOpdPrescriptions(visitId);

  const {
    startMutation,
    completeMutation,
    vitalsMutation,
    noteMutation,
    prescriptionMutation,
    isPending,
  } = useOpdConsultationActions(visitId);

  const readOnly = visit?.status === "completed" || visit?.status === "cancelled";
  const canStart = visit?.status === "waiting" && canConsult;
  const canComplete = visit?.status === "in_consultation" && canConsult;
  const isEditable = visit?.status === "in_consultation" && canConsult;

  const pageTitle = useMemo(() => {
    if (!visit) return "Doctor consultation";
    const patientName = visit.patient_name ?? "Patient";
    return `Consultation — ${patientName}`;
  }, [visit]);

  async function handleStart() {
    try {
      await startMutation.mutateAsync();
      toast.success("Consultation started");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to start consultation");
    }
  }

  async function handleComplete() {
    try {
      await completeMutation.mutateAsync({
        finalize_notes: true,
        create_billing_draft: true,
      });
      if (visitId) clearConsultationDraft(visitId);
      toast.success("Consultation completed");
      navigate("/opd/queue");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to complete consultation");
    }
  }

  if (visitQuery.isLoading) {
    return (
      <AdminPageFrame title="Doctor consultation" description="Loading visit…">
        <div className="h-48 animate-pulse rounded-xl bg-surface-secondary" />
      </AdminPageFrame>
    );
  }

  if (visitQuery.error || !visit) {
    return (
      <AdminPageFrame title="Doctor consultation" description="Visit not found">
        <Alert variant="error">
          {visitQuery.error instanceof ApiError
            ? visitQuery.error.message
            : "Unable to load this OPD visit."}
        </Alert>
        <Link to="/opd/queue" className="mt-4 inline-flex text-sm text-primary hover:underline">
          Back to OPD queue
        </Link>
      </AdminPageFrame>
    );
  }

  if (!canConsult) {
    return (
      <AdminPageFrame title="Doctor consultation" description="Insufficient permissions">
        <Alert variant="warning">
          Your account does not have permission to conduct consultations. Ask an administrator for
          the conduct consultation permission.
        </Alert>
      </AdminPageFrame>
    );
  }

  return (
    <AdminPageFrame
      title={pageTitle}
      description={`${visit.visit_number} · Token #${visit.token_number ?? "—"} · ${formatDate(visit.visit_date)}`}
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate("/opd/queue")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Queue
          </Button>
          {canStart && (
            <Button size="sm" onClick={handleStart} disabled={isPending}>
              <PlayCircle className="mr-2 h-4 w-4" />
              Start consultation
            </Button>
          )}
          {canComplete && (
            <Button size="sm" onClick={handleComplete} disabled={isPending}>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Complete visit
            </Button>
          )}
        </div>
      }
    >
      <div className="mb-6 flex flex-wrap items-center gap-3 text-sm">
        <OpdVisitStatusBadge status={visit.status} />
        <span className="text-muted">
          Doctor: {visit.doctor_name ?? "—"}
          {visit.location_name ? ` · ${visit.location_name}` : ""}
        </span>
        {visit.patient_name && (
          <span className="text-muted">
            Patient: {visit.patient_name}
            {visit.patient_mrn ? ` (${visit.patient_mrn})` : ""}
          </span>
        )}
      </div>

      {visit.status === "waiting" && (
        <Alert variant="info" className="mb-6">
          Start the consultation to record vitals, clinical notes, and prescriptions.
        </Alert>
      )}

      <FormPageLayout
        sidebar={
          <OpdConsultPatientPanel
            patient={patientQuery.data}
            visits={visitsQuery.data?.data ?? []}
            isLoading={patientQuery.isLoading || visitsQuery.isLoading}
          />
        }
      >
        {(isEditable || readOnly) && (
          <OpdConsultationWorkspace
            visitId={visitId}
            chiefComplaint={visit.chief_complaint}
            readOnly={readOnly || !isEditable}
            vitals={vitalsQuery.data ?? []}
            notes={notesQuery.data ?? []}
            prescriptions={prescriptionsQuery.data ?? []}
            allergies={patientQuery.data?.allergies ?? []}
            onSaveVitals={async (payload) => {
              await vitalsMutation.mutateAsync(payload);
            }}
            onSaveNotes={async (payloads) => {
              for (const payload of payloads) {
                await noteMutation.mutateAsync({
                  note_type: payload.note_type as OpdNoteType,
                  content: payload.content,
                });
              }
            }}
            onSavePrescription={async (payload) => {
              if (!canPrescribe) {
                toast.error("You do not have permission to prescribe medications.");
                return;
              }
              await prescriptionMutation.mutateAsync(payload);
            }}
            isSaving={isPending}
          />
        )}
      </FormPageLayout>
    </AdminPageFrame>
  );
}
