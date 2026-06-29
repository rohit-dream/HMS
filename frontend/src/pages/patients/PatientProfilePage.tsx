import { useState, type FormEvent, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { HeartPulse, Phone, UserRound, Users } from "lucide-react";
import {
  addPatientAllergyRequest,
  addPatientChronicConditionRequest,
  addPatientContactRequest,
  deletePatientAllergyRequest,
} from "@/api/endpoints/patients";
import { ApiError } from "@/api/errors";
import type {
  PatientAllergy,
  PatientChronicCondition,
  PatientContact,
  PatientDetail,
} from "@/api/types/patients";
import { AdminPageFrame, EmptyState } from "@/components/enterprise";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import {
  Alert,
  Badge,
  Button,
  FieldLabel,
  Input,
  Modal,
  Select,
  primaryLinkClassName,
  useToast,
} from "@/components/ui";
import { GlassCard } from "@/components/ui/GlassCard";
import { PatientVisitHistoryTable } from "@/features/patients/components/PatientVisitHistoryTable";
import { usePatient } from "@/features/patients/hooks/usePatient";
import { usePatientVisits } from "@/features/patients/hooks/usePatientVisits";
import {
  calculateAge,
  formatDate,
  formatPatientName,
  formatPhone,
  genderLabel,
} from "@/lib/formatters";

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-muted">{label}</dt>
      <dd className="mt-1 font-medium text-foreground">{value ?? "—"}</dd>
    </div>
  );
}

function formatAddress(patient: PatientDetail): string | null {
  const parts = [patient.address_line1, patient.city, patient.state, patient.postal_code].filter(
    Boolean,
  );
  return parts.length > 0 ? parts.join(", ") : null;
}

function severityVariant(severity: string): "success" | "warning" | "error" | "neutral" {
  if (severity === "severe") return "error";
  if (severity === "moderate") return "warning";
  if (severity === "mild") return "success";
  return "neutral";
}

function conditionStatusVariant(status: string): "success" | "warning" | "error" | "neutral" {
  if (status === "active") return "warning";
  if (status === "resolved") return "success";
  return "neutral";
}

function consentMethodLabel(method: string | null): string {
  if (!method) return "—";
  if (method === "digital") return "Digital / form";
  if (method === "written") return "Written";
  if (method === "verbal") return "Verbal";
  return method;
}

export function PatientProfilePage() {
  const { patientId } = useParams<{ patientId: string }>();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [visitPage, setVisitPage] = useState(1);
  const [allergyModalOpen, setAllergyModalOpen] = useState(false);
  const [contactModalOpen, setContactModalOpen] = useState(false);
  const [conditionModalOpen, setConditionModalOpen] = useState(false);

  const patientQuery = usePatient(patientId);
  const visitsQuery = usePatientVisits(patientId, visitPage, 10);

  const invalidatePatient = async () => {
    await queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
    await queryClient.invalidateQueries({ queryKey: ["patients"] });
  };

  const deleteAllergyMutation = useMutation({
    mutationFn: (allergyId: string) => deletePatientAllergyRequest(patientId!, allergyId),
    onSuccess: async () => {
      await invalidatePatient();
      toast.success("Allergy removed.");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Failed to remove allergy.");
    },
  });

  if (patientQuery.isLoading) {
    return (
      <AdminPageFrame title="Patient profile" description="Loading patient record…">
        <GlassCard strong className="animate-pulse space-y-4 p-6">
          <div className="h-6 w-48 rounded bg-surface-secondary" />
          <div className="h-4 w-full max-w-md rounded bg-surface-secondary" />
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="h-16 rounded bg-surface-secondary" />
            <div className="h-16 rounded bg-surface-secondary" />
          </div>
        </GlassCard>
      </AdminPageFrame>
    );
  }

  if (patientQuery.isError) {
    return (
      <AdminPageFrame title="Unable to load patient" description="Something went wrong.">
        <Alert variant="error">
          {patientQuery.error instanceof ApiError
            ? patientQuery.error.message
            : "Failed to load patient profile."}
        </Alert>
        <Link to="/patients" className={`${primaryLinkClassName} mt-4 inline-flex`}>
          Back to patients
        </Link>
      </AdminPageFrame>
    );
  }

  const patient = patientQuery.data;
  if (!patient) {
    return (
      <AdminPageFrame title="Patient not found" description="The requested patient record does not exist.">
        <Alert variant="error">Patient not found.</Alert>
        <Link to="/patients" className={`${primaryLinkClassName} mt-4 inline-flex`}>
          Back to patients
        </Link>
      </AdminPageFrame>
    );
  }

  const visits = visitsQuery.data?.data ?? [];
  const visitPagination = visitsQuery.data?.pagination;

  return (
    <AdminPageFrame
      title={formatPatientName(patient.first_name, patient.last_name)}
      description={`${patient.mrn} · ${formatPhone(patient.phone)}`}
      actions={
        <Link to="/patients" className={primaryLinkClassName}>
          Back to patients
        </Link>
      }
    >
      <div className="grid gap-6 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-4">
          <GlassCard strong className="text-sm">
            <h3 className="text-base font-semibold text-foreground">Patient summary</h3>
            <dl className="mt-4 grid gap-4">
              <DetailRow label="MRN" value={<span className="font-mono text-xs">{patient.mrn}</span>} />
              <DetailRow
                label="Age / DOB"
                value={`${calculateAge(patient.date_of_birth)} yrs · ${formatDate(patient.date_of_birth)}`}
              />
              <DetailRow label="Gender" value={genderLabel(patient.gender)} />
              <DetailRow label="Blood group" value={patient.blood_group} />
              <DetailRow label="Phone" value={formatPhone(patient.phone)} />
              <DetailRow label="Email" value={patient.email} />
              <DetailRow label="Last visit" value={formatDate(patient.last_visit_date)} />
              <DetailRow
                label="Consent"
                value={
                  patient.consent_given_at ? (
                    <span>
                      {consentMethodLabel(patient.consent_method)} ·{" "}
                      {formatDate(patient.consent_given_at)}
                    </span>
                  ) : (
                    "—"
                  )
                }
              />
            </dl>
          </GlassCard>
        </div>

        <div className="space-y-6 lg:col-span-8">
          <GlassCard strong className="text-sm">
            <h3 className="text-base font-semibold text-foreground">Demographics</h3>
            <dl className="mt-4 grid gap-4 sm:grid-cols-2">
              <DetailRow label="Marital status" value={patient.marital_status} />
              <DetailRow label="Occupation" value={patient.occupation} />
              <DetailRow label="Address" value={formatAddress(patient)} />
              <DetailRow
                label="ID proof"
                value={
                  patient.id_proof_type
                    ? `${patient.id_proof_type}${patient.id_proof_number ? ` · ${patient.id_proof_number}` : ""}`
                    : null
                }
              />
              <DetailRow label="Registered" value={formatDate(patient.created_at)} />
              <DetailRow label="Last updated" value={formatDate(patient.updated_at)} />
            </dl>
          </GlassCard>

          <ClinicalSection
            title="Allergies"
            description="Active and historical allergen records."
            emptyTitle="No allergies recorded"
            emptyDescription="Document known allergens to support safer prescribing and care."
            action={
              <PermissionGuard permission="patient:update">
                <Button type="button" size="sm" onClick={() => setAllergyModalOpen(true)}>
                  Add allergy
                </Button>
              </PermissionGuard>
            }
          >
            {patient.allergies.length === 0 ? (
              <EmptyState icon={HeartPulse} title="No allergies recorded" description="" />
            ) : (
              <ul className="divide-y divide-border-light">
                {patient.allergies.map((allergy) => (
                  <AllergyRow
                    key={allergy.id}
                    allergy={allergy}
                    onDelete={() => {
                      if (window.confirm(`Remove allergy "${allergy.allergen}"?`)) {
                        deleteAllergyMutation.mutate(allergy.id);
                      }
                    }}
                    deleting={deleteAllergyMutation.isPending}
                  />
                ))}
              </ul>
            )}
          </ClinicalSection>

          <ClinicalSection
            title="Emergency contacts"
            description="Family members and guardians linked to this patient."
            emptyTitle="No contacts recorded"
            emptyDescription="Add at least one emergency contact for outreach."
            action={
              <PermissionGuard permission="patient:update">
                <Button type="button" size="sm" onClick={() => setContactModalOpen(true)}>
                  Add contact
                </Button>
              </PermissionGuard>
            }
          >
            {patient.contacts.length === 0 ? (
              <EmptyState icon={Users} title="No contacts recorded" description="" />
            ) : (
              <ul className="divide-y divide-border-light">
                {patient.contacts.map((contact) => (
                  <ContactRow key={contact.id} contact={contact} />
                ))}
              </ul>
            )}
          </ClinicalSection>

          <ClinicalSection
            title="Chronic conditions"
            description="Long-term diagnoses tracked on the patient chart."
            emptyTitle="No chronic conditions"
            emptyDescription="Record ongoing conditions such as diabetes or hypertension."
            action={
              <PermissionGuard permission="patient:update">
                <Button type="button" size="sm" onClick={() => setConditionModalOpen(true)}>
                  Add condition
                </Button>
              </PermissionGuard>
            }
          >
            {patient.chronic_conditions.length === 0 ? (
              <EmptyState icon={UserRound} title="No chronic conditions" description="" />
            ) : (
              <ul className="divide-y divide-border-light">
                {patient.chronic_conditions.map((condition) => (
                  <ConditionRow key={condition.id} condition={condition} />
                ))}
              </ul>
            )}
          </ClinicalSection>

          <GlassCard strong className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-foreground">Visit history</h3>
              <p className="mt-1 text-sm text-muted">
                Chronological OPD visits with complaint, diagnosis, and visit summary.
              </p>
            </div>

            <PatientVisitHistoryTable
              visits={visits}
              isLoading={visitsQuery.isLoading}
              pagination={visitPagination}
              onPageChange={setVisitPage}
              errorMessage={
                visitsQuery.isError
                  ? visitsQuery.error instanceof ApiError
                    ? visitsQuery.error.message
                    : "Failed to load visit history."
                  : null
              }
            />
          </GlassCard>
        </div>
      </div>

      {patientId && (
        <>
          <AddAllergyModal
            open={allergyModalOpen}
            patientId={patientId}
            onClose={() => setAllergyModalOpen(false)}
            onSuccess={async () => {
              await invalidatePatient();
              setAllergyModalOpen(false);
              toast.success("Allergy added.");
            }}
          />
          <AddContactModal
            open={contactModalOpen}
            patientId={patientId}
            onClose={() => setContactModalOpen(false)}
            onSuccess={async () => {
              await invalidatePatient();
              setContactModalOpen(false);
              toast.success("Contact added.");
            }}
          />
          <AddChronicConditionModal
            open={conditionModalOpen}
            patientId={patientId}
            onClose={() => setConditionModalOpen(false)}
            onSuccess={async () => {
              await invalidatePatient();
              setConditionModalOpen(false);
              toast.success("Chronic condition recorded.");
            }}
          />
        </>
      )}
    </AdminPageFrame>
  );
}

function ClinicalSection({
  title,
  description,
  action,
  children,
}: {
  title: string;
  description: string;
  action?: ReactNode;
  children: ReactNode;
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  return (
    <GlassCard strong className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-foreground">{title}</h3>
          <p className="mt-1 text-sm text-muted">{description}</p>
        </div>
        {action}
      </div>
      {children}
    </GlassCard>
  );
}

function AllergyRow({
  allergy,
  onDelete,
  deleting,
}: {
  allergy: PatientAllergy;
  onDelete: () => void;
  deleting: boolean;
}) {
  return (
    <li className="flex flex-wrap items-start justify-between gap-3 py-3 text-sm">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-foreground">{allergy.allergen}</span>
          <Badge variant={severityVariant(allergy.severity)} className="capitalize">
            {allergy.severity}
          </Badge>
          {!allergy.is_active && <Badge variant="neutral">Inactive</Badge>}
        </div>
        {allergy.reaction && <p className="mt-1 text-muted">Reaction: {allergy.reaction}</p>}
        {allergy.onset_date && (
          <p className="mt-1 text-xs text-muted">Onset {formatDate(allergy.onset_date)}</p>
        )}
      </div>
      <PermissionGuard permission="patient:update">
        <Button type="button" variant="ghost" size="sm" disabled={deleting} onClick={onDelete}>
          Remove
        </Button>
      </PermissionGuard>
    </li>
  );
}

function ContactRow({ contact }: { contact: PatientContact }) {
  return (
    <li className="py-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-foreground">{contact.name}</span>
        <Badge variant="neutral" className="capitalize">
          {contact.relationship}
        </Badge>
        {contact.is_primary && <Badge variant="info">Primary</Badge>}
        {contact.is_emergency && <Badge variant="warning">Emergency</Badge>}
      </div>
      <p className="mt-1 text-muted">
        <Phone className="mr-1 inline h-3.5 w-3.5" aria-hidden />
        {formatPhone(contact.phone)}
        {contact.email ? ` · ${contact.email}` : ""}
      </p>
    </li>
  );
}

function ConditionRow({ condition }: { condition: PatientChronicCondition }) {
  return (
    <li className="py-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-foreground">{condition.condition_name}</span>
        <Badge variant={conditionStatusVariant(condition.status)} className="capitalize">
          {condition.status}
        </Badge>
        {condition.icd_code && (
          <span className="font-mono text-xs text-muted">ICD {condition.icd_code}</span>
        )}
      </div>
      {condition.diagnosed_date && (
        <p className="mt-1 text-xs text-muted">Diagnosed {formatDate(condition.diagnosed_date)}</p>
      )}
      {condition.notes && <p className="mt-1 text-muted">{condition.notes}</p>}
    </li>
  );
}

function AddAllergyModal({
  open,
  patientId,
  onClose,
  onSuccess,
}: {
  open: boolean;
  patientId: string;
  onClose: () => void;
  onSuccess: () => Promise<void>;
}) {
  const [allergen, setAllergen] = useState("");
  const [severity, setSeverity] = useState<"mild" | "moderate" | "severe">("moderate");
  const [reaction, setReaction] = useState("");
  const [onsetDate, setOnsetDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!allergen.trim()) {
      setError("Allergen is required.");
      return;
    }
    setSaving(true);
    try {
      await addPatientAllergyRequest(patientId, {
        allergen: allergen.trim(),
        severity,
        reaction: reaction.trim() || undefined,
        onset_date: onsetDate || undefined,
      });
      setAllergen("");
      setReaction("");
      setOnsetDate("");
      await onSuccess();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add allergy.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={open}
      title="Add allergy"
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="add-allergy-form" disabled={saving}>
            {saving ? "Saving…" : "Add allergy"}
          </Button>
        </div>
      }
    >
      <form id="add-allergy-form" className="space-y-4" onSubmit={handleSubmit}>
        {error && <Alert variant="error">{error}</Alert>}
        <div className="space-y-1.5">
          <FieldLabel htmlFor="allergen" label="Allergen" />
          <Input id="allergen" value={allergen} onChange={(e) => setAllergen(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="severity" label="Severity" />
          <Select id="severity" value={severity} onChange={(e) => setSeverity(e.target.value as typeof severity)}>
            <option value="mild">Mild</option>
            <option value="moderate">Moderate</option>
            <option value="severe">Severe</option>
          </Select>
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="reaction" label="Reaction (optional)" />
          <Input id="reaction" value={reaction} onChange={(e) => setReaction(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="onset_date" label="Onset date (optional)" />
          <Input
            id="onset_date"
            type="date"
            value={onsetDate}
            onChange={(e) => setOnsetDate(e.target.value)}
          />
        </div>
      </form>
    </Modal>
  );
}

function AddContactModal({
  open,
  patientId,
  onClose,
  onSuccess,
}: {
  open: boolean;
  patientId: string;
  onClose: () => void;
  onSuccess: () => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [relationship, setRelationship] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [isEmergency, setIsEmergency] = useState(true);
  const [isPrimary, setIsPrimary] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!name.trim() || !relationship.trim()) {
      setError("Name and relationship are required.");
      return;
    }
    if (!/^\d{10}$/.test(phone.trim())) {
      setError("Phone must be exactly 10 digits.");
      return;
    }
    setSaving(true);
    try {
      await addPatientContactRequest(patientId, {
        name: name.trim(),
        relationship: relationship.trim(),
        phone: phone.trim(),
        email: email.trim() || undefined,
        is_emergency: isEmergency,
        is_primary: isPrimary,
      });
      setName("");
      setRelationship("");
      setPhone("");
      setEmail("");
      await onSuccess();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add contact.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={open}
      title="Add contact"
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="add-contact-form" disabled={saving}>
            {saving ? "Saving…" : "Add contact"}
          </Button>
        </div>
      }
    >
      <form id="add-contact-form" className="space-y-4" onSubmit={handleSubmit}>
        {error && <Alert variant="error">{error}</Alert>}
        <div className="space-y-1.5">
          <FieldLabel htmlFor="contact_name" label="Name" />
          <Input id="contact_name" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="relationship" label="Relationship" />
          <Input
            id="relationship"
            value={relationship}
            onChange={(e) => setRelationship(e.target.value)}
            placeholder="e.g. spouse, parent, guardian"
          />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="contact_phone" label="Phone" />
          <Input id="contact_phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="contact_email" label="Email (optional)" />
          <Input
            id="contact_email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isEmergency}
            onChange={(e) => setIsEmergency(e.target.checked)}
          />
          Emergency contact
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={isPrimary} onChange={(e) => setIsPrimary(e.target.checked)} />
          Primary contact
        </label>
      </form>
    </Modal>
  );
}

function AddChronicConditionModal({
  open,
  patientId,
  onClose,
  onSuccess,
}: {
  open: boolean;
  patientId: string;
  onClose: () => void;
  onSuccess: () => Promise<void>;
}) {
  const [conditionName, setConditionName] = useState("");
  const [icdCode, setIcdCode] = useState("");
  const [diagnosedDate, setDiagnosedDate] = useState("");
  const [status, setStatus] = useState<"active" | "resolved" | "inactive">("active");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!conditionName.trim()) {
      setError("Condition name is required.");
      return;
    }
    setSaving(true);
    try {
      await addPatientChronicConditionRequest(patientId, {
        condition_name: conditionName.trim(),
        icd_code: icdCode.trim() || undefined,
        diagnosed_date: diagnosedDate || undefined,
        status,
        notes: notes.trim() || undefined,
      });
      setConditionName("");
      setIcdCode("");
      setDiagnosedDate("");
      setNotes("");
      await onSuccess();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add condition.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={open}
      title="Add chronic condition"
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="add-condition-form" disabled={saving}>
            {saving ? "Saving…" : "Add condition"}
          </Button>
        </div>
      }
    >
      <form id="add-condition-form" className="space-y-4" onSubmit={handleSubmit}>
        {error && <Alert variant="error">{error}</Alert>}
        <div className="space-y-1.5">
          <FieldLabel htmlFor="condition_name" label="Condition name" />
          <Input
            id="condition_name"
            value={conditionName}
            onChange={(e) => setConditionName(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="icd_code" label="ICD code (optional)" />
          <Input id="icd_code" value={icdCode} onChange={(e) => setIcdCode(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="diagnosed_date" label="Diagnosed date (optional)" />
          <Input
            id="diagnosed_date"
            type="date"
            value={diagnosedDate}
            onChange={(e) => setDiagnosedDate(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="condition_status" label="Status" />
          <Select
            id="condition_status"
            value={status}
            onChange={(e) => setStatus(e.target.value as typeof status)}
          >
            <option value="active">Active</option>
            <option value="resolved">Resolved</option>
            <option value="inactive">Inactive</option>
          </Select>
        </div>
        <div className="space-y-1.5">
          <FieldLabel htmlFor="condition_notes" label="Notes (optional)" />
          <Input id="condition_notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
      </form>
    </Modal>
  );
}
