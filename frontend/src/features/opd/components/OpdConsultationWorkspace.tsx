import { useEffect, useMemo, useState } from "react";
import { z } from "zod";
import { AlertTriangle, CheckCircle2, Plus, Trash2 } from "lucide-react";
import type { OpdClinicalNote, OpdPrescription, OpdVitals } from "@/api/types/opd";
import type { PatientAllergy } from "@/api/types/patients";
import { FormSection } from "@/components/enterprise";
import { Alert, Button, FieldLabel, Input, Select, useToast } from "@/components/ui";
import {
  loadConsultationDraft,
  useConsultationDraftAutosave,
} from "@/features/opd/hooks/useConsultationDraft";
import {
  emptyPrescriptionItem,
  toOpdPrescriptionPayload,
  type ConsultationPrescriptionFormValues,
  type PrescriptionItemFormValues,
} from "@/features/opd/schemas/consultationPrescriptionSchema";
import {
  toOpdVitalsPayload,
  type ConsultationVitalsFormValues,
} from "@/features/opd/schemas/consultationVitalsSchema";
import {
  notePayloadsFromForm,
  notesFromRecords,
  type ConsultationNotesFormState,
} from "@/features/opd/utils/consultationNotes";

const textareaClassName =
  "glass-textarea min-h-[6rem] w-full rounded-lg border border-border-light bg-card px-3 py-2 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30";

function vitalsToForm(vitals: OpdVitals | undefined): ConsultationVitalsFormValues {
  if (!vitals) {
    return {
      blood_pressure_systolic: "",
      blood_pressure_diastolic: "",
      pulse_rate: "",
      temperature: "",
      respiratory_rate: "",
      spo2: "",
      weight_kg: "",
      height_cm: "",
      notes: "",
    };
  }

  return {
    blood_pressure_systolic: vitals.blood_pressure_systolic?.toString() ?? "",
    blood_pressure_diastolic: vitals.blood_pressure_diastolic?.toString() ?? "",
    pulse_rate: vitals.pulse_rate?.toString() ?? "",
    temperature: vitals.temperature?.toString() ?? "",
    respiratory_rate: vitals.respiratory_rate?.toString() ?? "",
    spo2: vitals.spo2?.toString() ?? "",
    weight_kg: vitals.weight_kg?.toString() ?? "",
    height_cm: vitals.height_cm?.toString() ?? "",
    notes: vitals.notes ?? "",
  };
}

function findAllergyWarnings(
  items: PrescriptionItemFormValues[],
  allergies: PatientAllergy[],
): string[] {
  const active = allergies.filter((allergy) => allergy.is_active);
  const warnings: string[] = [];

  for (const item of items) {
    const drug = item.medicine_name.trim().toLowerCase();
    if (!drug) continue;
    for (const allergy of active) {
      const allergen = allergy.allergen.trim().toLowerCase();
      if (allergen && (drug.includes(allergen) || allergen.includes(drug))) {
        warnings.push(`${item.medicine_name} may conflict with allergy: ${allergy.allergen}`);
      }
    }
  }

  return warnings;
}

interface OpdConsultationWorkspaceProps {
  visitId?: string;
  chiefComplaint: string | null;
  readOnly: boolean;
  vitals: OpdVitals[];
  notes: OpdClinicalNote[];
  prescriptions: OpdPrescription[];
  allergies: PatientAllergy[];
  draftVitals?: Record<string, string>;
  draftNotes?: ConsultationNotesFormState;
  onSaveVitals: (payload: ReturnType<typeof toOpdVitalsPayload>) => Promise<void>;
  onSaveNotes: (payloads: Array<{ note_type: string; content: string }>) => Promise<void>;
  onSavePrescription: (payload: ReturnType<typeof toOpdPrescriptionPayload>) => Promise<void>;
  isSaving: boolean;
}

export function OpdConsultationWorkspace({
  visitId,
  chiefComplaint,
  readOnly,
  vitals,
  notes,
  prescriptions,
  allergies,
  draftVitals,
  draftNotes,
  onSaveVitals,
  onSaveNotes,
  onSavePrescription,
  isSaving,
}: OpdConsultationWorkspaceProps) {
  const toast = useToast();
  const latestVitals = vitals[0];
  const storedDraft = useMemo(
    () => (visitId && !readOnly ? loadConsultationDraft(visitId) : null),
    [visitId, readOnly],
  );

  const [vitalsForm, setVitalsForm] = useState<ConsultationVitalsFormValues>(() =>
    draftVitals
      ? { ...vitalsToForm(latestVitals), ...draftVitals }
      : storedDraft?.vitals
        ? { ...vitalsToForm(latestVitals), ...storedDraft.vitals }
        : vitalsToForm(latestVitals),
  );
  const [savedNotes, setSavedNotes] = useState<ConsultationNotesFormState>(() =>
    notesFromRecords(notes),
  );
  const [notesForm, setNotesForm] = useState<ConsultationNotesFormState>(() => {
    if (draftNotes) return draftNotes;
    if (storedDraft?.notes) return storedDraft.notes;
    return notesFromRecords(notes);
  });
  const [vitalsError, setVitalsError] = useState<string | null>(null);
  const [prescriptionForm, setPrescriptionForm] = useState<ConsultationPrescriptionFormValues>(() => {
    if (storedDraft?.prescriptionItems?.length) {
      return {
        notes: storedDraft.prescriptionNotes ?? "",
        items: storedDraft.prescriptionItems.map((item) => ({
          medicine_name: item.medicine_name ?? "",
          dosage: item.dosage ?? "",
          frequency: item.frequency ?? "",
          duration: item.duration ?? "",
          route: (item.route as PrescriptionItemFormValues["route"]) ?? "oral",
          instructions: item.instructions ?? "",
          quantity: item.quantity ?? "",
        })),
      };
    }
    return { notes: "", items: [emptyPrescriptionItem()] };
  });
  const [prescriptionError, setPrescriptionError] = useState<string | null>(null);

  useEffect(() => {
    setSavedNotes(notesFromRecords(notes));
    if (!draftNotes) {
      setNotesForm(notesFromRecords(notes));
    }
  }, [notes, draftNotes]);

  useEffect(() => {
    if (!draftVitals) {
      setVitalsForm(vitalsToForm(latestVitals));
    }
  }, [latestVitals, draftVitals]);

  const allergyWarnings = useMemo(
    () => findAllergyWarnings(prescriptionForm.items, allergies),
    [prescriptionForm.items, allergies],
  );

  const draftSnapshot = useMemo(
    () => ({
      vitals: vitalsForm as Record<string, string>,
      notes: notesForm,
      prescriptionNotes: prescriptionForm.notes ?? "",
      prescriptionItems: prescriptionForm.items.map((item) => ({
        medicine_name: item.medicine_name,
        dosage: item.dosage,
        frequency: item.frequency,
        duration: item.duration,
        route: item.route ?? "oral",
        instructions: item.instructions ?? "",
        quantity: String(item.quantity ?? ""),
      })),
      savedAt: "",
    }),
    [vitalsForm, notesForm, prescriptionForm],
  );

  useConsultationDraftAutosave(visitId, draftSnapshot, Boolean(visitId) && !readOnly);

  async function handleSaveVitals(event: React.FormEvent) {
    event.preventDefault();
    if (readOnly) return;

    try {
      const payload = toOpdVitalsPayload(vitalsForm);
      setVitalsError(null);
      await onSaveVitals(payload);
      toast.success("Vitals saved");
    } catch (error) {
      if (error instanceof z.ZodError) {
        setVitalsError(error.issues[0]?.message ?? "Invalid vitals");
      } else {
        toast.error("Unable to save vitals");
      }
    }
  }

  async function handleSaveNotes(event: React.FormEvent) {
    event.preventDefault();
    if (readOnly) return;

    const payloads = notePayloadsFromForm(notesForm, savedNotes);
    if (payloads.length === 0) {
      toast.info("No note changes to save");
      return;
    }

    try {
      await onSaveNotes(payloads);
      setSavedNotes({ ...notesForm });
      toast.success("Clinical notes saved");
    } catch {
      toast.error("Unable to save notes");
    }
  }

  async function handleSavePrescription(event: React.FormEvent) {
    event.preventDefault();
    if (readOnly) return;

    try {
      const payload = toOpdPrescriptionPayload(prescriptionForm);
      setPrescriptionError(null);
      await onSavePrescription(payload);
      setPrescriptionForm({ notes: "", items: [emptyPrescriptionItem()] });
      toast.success("Prescription saved");
    } catch (error) {
      if (error instanceof z.ZodError) {
        setPrescriptionError(error.issues[0]?.message ?? "Invalid prescription");
      } else {
        toast.error("Unable to save prescription");
      }
    }
  }

  function updatePrescriptionItem(index: number, patch: Partial<PrescriptionItemFormValues>) {
    setPrescriptionForm((current) => ({
      ...current,
      items: current.items.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item,
      ),
    }));
  }

  return (
    <div className="space-y-8">
      <FormSection
        title="Chief complaint"
        description="Recorded when the visit was created."
        columns={1}
      >
        <p className="rounded-lg border border-border-light bg-card/60 px-4 py-3 text-sm text-foreground">
          {chiefComplaint?.trim() || "No chief complaint recorded."}
        </p>
      </FormSection>

      <form className="space-y-4" onSubmit={handleSaveVitals}>
        <FormSection
          title="Vitals"
          description="Blood pressure, pulse, temperature, weight, height, and SpO₂."
        >
          <div>
            <FieldLabel htmlFor="bp-sys">BP systolic (mmHg)</FieldLabel>
            <Input
              id="bp-sys"
              type="number"
              value={vitalsForm.blood_pressure_systolic ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({
                  ...current,
                  blood_pressure_systolic: event.target.value,
                }))
              }
              disabled={readOnly}
            />
          </div>
          <div>
            <FieldLabel htmlFor="bp-dia">BP diastolic (mmHg)</FieldLabel>
            <Input
              id="bp-dia"
              type="number"
              value={vitalsForm.blood_pressure_diastolic ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({
                  ...current,
                  blood_pressure_diastolic: event.target.value,
                }))
              }
              disabled={readOnly}
            />
          </div>
          <div>
            <FieldLabel htmlFor="pulse">Pulse (bpm)</FieldLabel>
            <Input
              id="pulse"
              type="number"
              value={vitalsForm.pulse_rate ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({ ...current, pulse_rate: event.target.value }))
              }
              disabled={readOnly}
            />
          </div>
          <div>
            <FieldLabel htmlFor="temperature">Temperature (°C)</FieldLabel>
            <Input
              id="temperature"
              type="number"
              step="0.1"
              value={vitalsForm.temperature ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({ ...current, temperature: event.target.value }))
              }
              disabled={readOnly}
            />
          </div>
          <div>
            <FieldLabel htmlFor="respiratory">Respiratory rate</FieldLabel>
            <Input
              id="respiratory"
              type="number"
              value={vitalsForm.respiratory_rate ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({
                  ...current,
                  respiratory_rate: event.target.value,
                }))
              }
              disabled={readOnly}
            />
          </div>
          <div>
            <FieldLabel htmlFor="spo2">SpO₂ (%)</FieldLabel>
            <Input
              id="spo2"
              type="number"
              value={vitalsForm.spo2 ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({ ...current, spo2: event.target.value }))
              }
              disabled={readOnly}
            />
          </div>
          <div>
            <FieldLabel htmlFor="weight">Weight (kg)</FieldLabel>
            <Input
              id="weight"
              type="number"
              step="0.1"
              value={vitalsForm.weight_kg ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({ ...current, weight_kg: event.target.value }))
              }
              disabled={readOnly}
            />
          </div>
          <div>
            <FieldLabel htmlFor="height">Height (cm)</FieldLabel>
            <Input
              id="height"
              type="number"
              step="0.1"
              value={vitalsForm.height_cm ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({ ...current, height_cm: event.target.value }))
              }
              disabled={readOnly}
            />
          </div>
          <div className="md:col-span-2">
            <FieldLabel htmlFor="vitals-notes">Vitals notes</FieldLabel>
            <textarea
              id="vitals-notes"
              className={textareaClassName}
              value={vitalsForm.notes ?? ""}
              onChange={(event) =>
                setVitalsForm((current) => ({ ...current, notes: event.target.value }))
              }
              disabled={readOnly}
            />
          </div>
        </FormSection>
        {vitalsError && <p className="text-sm text-error">{vitalsError}</p>}
        {!readOnly && (
          <div className="flex justify-end">
            <Button type="submit" disabled={isSaving}>
              Save vitals
            </Button>
          </div>
        )}
      </form>

      {latestVitals?.bmi != null && (
        <p className="text-sm text-muted">Latest BMI: {latestVitals.bmi}</p>
      )}

      <form className="space-y-4" onSubmit={handleSaveNotes}>
        <FormSection
          title="Clinical notes"
          description="Examination findings, diagnosis, and treatment plan."
          columns={1}
        >
          {(["examination", "diagnosis", "plan", "general"] as const).map((noteType) => (
            <div key={noteType}>
              <FieldLabel htmlFor={`note-${noteType}`}>
                {noteType.charAt(0).toUpperCase() + noteType.slice(1)}
              </FieldLabel>
              <textarea
                id={`note-${noteType}`}
                className={textareaClassName}
                value={notesForm[noteType]}
                onChange={(event) =>
                  setNotesForm((current) => ({ ...current, [noteType]: event.target.value }))
                }
                disabled={readOnly}
                placeholder={
                  noteType === "diagnosis"
                    ? "Primary diagnosis and clinical impression"
                    : undefined
                }
              />
            </div>
          ))}
        </FormSection>
        {!readOnly && (
          <div className="flex justify-end">
            <Button type="submit" disabled={isSaving}>
              Save notes
            </Button>
          </div>
        )}
      </form>

      {prescriptions.length > 0 && (
        <FormSection title="Saved prescriptions" columns={1}>
          <ul className="space-y-3 text-sm">
            {prescriptions.map((prescription) => (
              <li
                key={prescription.id}
                className="rounded-lg border border-border-light bg-card/60 px-4 py-3"
              >
                <p className="font-medium text-foreground">{prescription.prescription_number}</p>
                <ul className="mt-2 space-y-1 text-muted">
                  {prescription.items.map((item) => (
                    <li key={item.id}>
                      {item.medicine_name} — {item.dosage}, {item.frequency}, {item.duration}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </FormSection>
      )}

      {!readOnly && (
        <form className="space-y-4" onSubmit={handleSavePrescription}>
          <FormSection
            title="E-prescription"
            description="Add medications for this consultation."
            columns={1}
          >
            {allergyWarnings.length > 0 && (
              <Alert variant="warning">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <ul className="space-y-1 text-sm">
                    {allergyWarnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </div>
              </Alert>
            )}

            {prescriptionForm.items.map((item, index) => (
              <div
                key={index}
                className="grid gap-4 rounded-xl border border-border-light bg-card/40 p-4 md:grid-cols-2"
              >
                <div className="md:col-span-2 flex items-center justify-between">
                  <p className="text-sm font-medium text-foreground">Medication {index + 1}</p>
                  {prescriptionForm.items.length > 1 && (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setPrescriptionForm((current) => ({
                          ...current,
                          items: current.items.filter((_, itemIndex) => itemIndex !== index),
                        }))
                      }
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
                <div className="md:col-span-2">
                  <FieldLabel htmlFor={`medicine-${index}`}>Drug name</FieldLabel>
                  <Input
                    id={`medicine-${index}`}
                    value={item.medicine_name}
                    onChange={(event) =>
                      updatePrescriptionItem(index, { medicine_name: event.target.value })
                    }
                  />
                </div>
                <div>
                  <FieldLabel htmlFor={`dosage-${index}`}>Dosage</FieldLabel>
                  <Input
                    id={`dosage-${index}`}
                    value={item.dosage}
                    onChange={(event) =>
                      updatePrescriptionItem(index, { dosage: event.target.value })
                    }
                    placeholder="500 mg"
                  />
                </div>
                <div>
                  <FieldLabel htmlFor={`frequency-${index}`}>Frequency</FieldLabel>
                  <Input
                    id={`frequency-${index}`}
                    value={item.frequency}
                    onChange={(event) =>
                      updatePrescriptionItem(index, { frequency: event.target.value })
                    }
                    placeholder="Twice daily"
                  />
                </div>
                <div>
                  <FieldLabel htmlFor={`duration-${index}`}>Duration</FieldLabel>
                  <Input
                    id={`duration-${index}`}
                    value={item.duration}
                    onChange={(event) =>
                      updatePrescriptionItem(index, { duration: event.target.value })
                    }
                    placeholder="5 days"
                  />
                </div>
                <div>
                  <FieldLabel htmlFor={`route-${index}`}>Route</FieldLabel>
                  <Select
                    id={`route-${index}`}
                    value={item.route ?? "oral"}
                    onChange={(event) =>
                      updatePrescriptionItem(index, {
                        route: event.target.value as PrescriptionItemFormValues["route"],
                      })
                    }
                  >
                    <option value="oral">Oral</option>
                    <option value="topical">Topical</option>
                    <option value="iv">IV</option>
                    <option value="im">IM</option>
                    <option value="sc">SC</option>
                    <option value="inhalation">Inhalation</option>
                    <option value="other">Other</option>
                  </Select>
                </div>
                <div className="md:col-span-2">
                  <FieldLabel htmlFor={`instructions-${index}`}>Instructions</FieldLabel>
                  <Input
                    id={`instructions-${index}`}
                    value={item.instructions ?? ""}
                    onChange={(event) =>
                      updatePrescriptionItem(index, { instructions: event.target.value })
                    }
                    placeholder="After meals"
                  />
                </div>
              </div>
            ))}

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                setPrescriptionForm((current) => ({
                  ...current,
                  items: [...current.items, emptyPrescriptionItem()],
                }))
              }
            >
              <Plus className="mr-2 h-4 w-4" />
              Add medication
            </Button>

            <div>
              <FieldLabel htmlFor="prescription-notes">Prescription notes</FieldLabel>
              <textarea
                id="prescription-notes"
                className={textareaClassName}
                value={prescriptionForm.notes ?? ""}
                onChange={(event) =>
                  setPrescriptionForm((current) => ({ ...current, notes: event.target.value }))
                }
              />
            </div>
          </FormSection>
          {prescriptionError && <p className="text-sm text-error">{prescriptionError}</p>}
          <div className="flex justify-end">
            <Button type="submit" disabled={isSaving}>
              Save prescription
            </Button>
          </div>
        </form>
      )}

      {readOnly && notes.length === 0 && vitals.length === 0 && prescriptions.length === 0 && (
        <Alert variant="info">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            This visit is completed. Clinical data is read-only.
          </div>
        </Alert>
      )}
    </div>
  );
}
