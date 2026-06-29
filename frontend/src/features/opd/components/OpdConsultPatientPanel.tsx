import { Link } from "react-router-dom";
import { AlertTriangle, ExternalLink, HeartPulse, History } from "lucide-react";
import type { PatientDetail, PatientVisitHistoryItem } from "@/api/types/patients";
import { EmptyState } from "@/components/enterprise";
import { Alert, Badge, primaryLinkClassName } from "@/components/ui";
import { GlassCard } from "@/components/ui/GlassCard";
import {
  calculateAge,
  formatDate,
  formatPatientName,
  formatPhone,
  genderLabel,
} from "@/lib/formatters";

interface OpdConsultPatientPanelProps {
  patient: PatientDetail | undefined;
  visits: PatientVisitHistoryItem[];
  isLoading: boolean;
}

function severityVariant(severity: string): "success" | "warning" | "error" | "neutral" {
  if (severity === "severe") return "error";
  if (severity === "moderate") return "warning";
  if (severity === "mild") return "success";
  return "neutral";
}

export function OpdConsultPatientPanel({
  patient,
  visits,
  isLoading,
}: OpdConsultPatientPanelProps) {
  if (isLoading) {
    return (
      <GlassCard strong padding="md" className="animate-pulse space-y-3">
        <div className="h-5 w-32 rounded bg-surface-secondary" />
        <div className="h-4 w-full rounded bg-surface-secondary" />
        <div className="h-4 w-2/3 rounded bg-surface-secondary" />
      </GlassCard>
    );
  }

  if (!patient) {
    return (
      <GlassCard strong padding="md">
        <p className="text-sm text-muted">Patient details unavailable.</p>
      </GlassCard>
    );
  }

  const activeAllergies = patient.allergies.filter((allergy) => allergy.is_active);

  return (
    <div className="space-y-4">
      <GlassCard strong padding="md">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Patient</p>
            <h3 className="mt-1 text-lg font-semibold text-foreground">
              {formatPatientName(patient.first_name, patient.last_name)}
            </h3>
            <p className="mt-1 text-sm text-muted">
              {patient.mrn} · {genderLabel(patient.gender)} · Age{" "}
              {calculateAge(patient.date_of_birth)}
            </p>
          </div>
          <Link
            to={`/patients/${patient.id}`}
            className={primaryLinkClassName}
            aria-label="Open full patient profile"
          >
            <ExternalLink className="h-4 w-4" />
          </Link>
        </div>

        <dl className="mt-4 space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Phone</dt>
            <dd className="font-medium text-foreground">{formatPhone(patient.phone)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Blood group</dt>
            <dd className="font-medium text-foreground">{patient.blood_group ?? "—"}</dd>
          </div>
        </dl>
      </GlassCard>

      {activeAllergies.length > 0 && (
        <Alert variant="error">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-medium">Active allergies</p>
              <ul className="mt-2 space-y-1 text-sm">
                {activeAllergies.map((allergy) => (
                  <li key={allergy.id}>
                    {allergy.allergen}
                    <Badge variant={severityVariant(allergy.severity)} className="ml-2">
                      {allergy.severity}
                    </Badge>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Alert>
      )}

      {patient.chronic_conditions.length > 0 && (
        <GlassCard padding="md">
          <div className="flex items-center gap-2">
            <HeartPulse className="h-4 w-4 text-primary" />
            <h4 className="text-sm font-semibold text-foreground">Chronic conditions</h4>
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            {patient.chronic_conditions.map((condition) => (
              <li key={condition.id} className="flex items-center justify-between gap-2">
                <span className="text-foreground">{condition.condition_name}</span>
                <Badge variant={condition.status === "active" ? "warning" : "neutral"}>
                  {condition.status}
                </Badge>
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      <GlassCard padding="md">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold text-foreground">Recent visits</h4>
        </div>
        {visits.length === 0 ? (
          <EmptyState
            className="mt-3 py-4"
            icon={History}
            title="No prior visits"
            description="This patient has no recorded visit history yet."
          />
        ) : (
          <ul className="mt-3 space-y-3 text-sm">
            {visits.slice(0, 5).map((visit) => (
              <li
                key={visit.id}
                className="border-b border-border-light pb-3 last:border-0 last:pb-0"
              >
                <Link
                  to={`/opd/visits/${visit.id}`}
                  className="group block rounded-md transition-colors hover:bg-hover/40"
                >
                  <p className="font-medium text-foreground group-hover:text-primary">
                    {formatDate(visit.visit_date)} · {visit.doctor_name}
                  </p>
                  <p className="mt-1 text-muted">
                    {visit.chief_complaint ?? "No complaint recorded"}
                  </p>
                  {visit.diagnosis && (
                    <p className="mt-1 text-xs text-foreground">Dx: {visit.diagnosis}</p>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </GlassCard>
    </div>
  );
}
