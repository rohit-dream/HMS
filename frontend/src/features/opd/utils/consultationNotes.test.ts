import { describe, expect, it } from "vitest";
import type { OpdClinicalNote } from "@/api/types/opd";
import {
  emptyConsultationNotes,
  notePayloadsFromForm,
  notesFromRecords,
} from "./consultationNotes";

function note(
  noteType: OpdClinicalNote["note_type"],
  content: string,
  createdAt: string,
): OpdClinicalNote {
  return {
    id: `${noteType}-${createdAt}`,
    opd_visit_id: "visit-1",
    note_type: noteType,
    content,
    icd_code: null,
    icd_description: null,
    is_final: false,
    created_by_user_id: "user-1",
    created_at: createdAt,
  };
}

describe("consultationNotes", () => {
  it("maps latest note per type from records", () => {
    const state = notesFromRecords([
      note("diagnosis", "Old diagnosis", "2026-06-01T10:00:00Z"),
      note("diagnosis", "Updated diagnosis", "2026-06-01T11:00:00Z"),
      note("plan", "Rest and fluids", "2026-06-01T09:00:00Z"),
    ]);

    expect(state.diagnosis).toBe("Updated diagnosis");
    expect(state.plan).toBe("Rest and fluids");
    expect(state.examination).toBe("");
  });

  it("returns payloads only for changed non-empty notes", () => {
    const saved = emptyConsultationNotes();
    const form = {
      ...saved,
      diagnosis: "Acute pharyngitis",
      plan: "Symptomatic care",
    };

    const payloads = notePayloadsFromForm(form, saved);
    expect(payloads).toEqual([
      { note_type: "diagnosis", content: "Acute pharyngitis" },
      { note_type: "plan", content: "Symptomatic care" },
    ]);
  });

  it("skips unchanged notes", () => {
    const saved = { ...emptyConsultationNotes(), diagnosis: "Same diagnosis" };
    const payloads = notePayloadsFromForm(saved, saved);
    expect(payloads).toEqual([]);
  });
});
