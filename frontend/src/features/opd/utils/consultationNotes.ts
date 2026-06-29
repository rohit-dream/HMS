import type { OpdClinicalNote, OpdNoteType } from "@/api/types/opd";

export interface ConsultationNotesFormState {
  examination: string;
  diagnosis: string;
  plan: string;
  general: string;
}

export const emptyConsultationNotes = (): ConsultationNotesFormState => ({
  examination: "",
  diagnosis: "",
  plan: "",
  general: "",
});

export function notesFromRecords(notes: OpdClinicalNote[]): ConsultationNotesFormState {
  const state = emptyConsultationNotes();
  const types: OpdNoteType[] = ["examination", "diagnosis", "plan", "general"];

  for (const noteType of types) {
    const latest = [...notes]
      .filter((note) => note.note_type === noteType)
      .sort((left, right) => right.created_at.localeCompare(left.created_at))[0];
    if (latest) {
      state[noteType] = latest.content;
    }
  }

  return state;
}

export function notePayloadsFromForm(
  form: ConsultationNotesFormState,
  saved: ConsultationNotesFormState,
): Array<{ note_type: OpdNoteType; content: string }> {
  const payloads: Array<{ note_type: OpdNoteType; content: string }> = [];
  const types: OpdNoteType[] = ["examination", "diagnosis", "plan", "general"];

  for (const noteType of types) {
    const content = form[noteType].trim();
    const previous = saved[noteType].trim();
    if (content.length > 0 && content !== previous) {
      payloads.push({ note_type: noteType, content });
    }
  }

  return payloads;
}
