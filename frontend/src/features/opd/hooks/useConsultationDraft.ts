import { useEffect, useRef } from "react";

const DRAFT_INTERVAL_MS = 30_000;

export interface ConsultationDraft {
  vitals: Record<string, string>;
  notes: {
    examination: string;
    diagnosis: string;
    plan: string;
    general: string;
  };
  prescriptionNotes: string;
  prescriptionItems: Array<Record<string, string>>;
  savedAt: string;
}

function draftKey(visitId: string) {
  return `opd-consult-draft:${visitId}`;
}

export function loadConsultationDraft(visitId: string): ConsultationDraft | null {
  try {
    const raw = localStorage.getItem(draftKey(visitId));
    if (!raw) return null;
    return JSON.parse(raw) as ConsultationDraft;
  } catch {
    return null;
  }
}

export function saveConsultationDraft(visitId: string, draft: ConsultationDraft) {
  localStorage.setItem(draftKey(visitId), JSON.stringify(draft));
}

export function clearConsultationDraft(visitId: string) {
  localStorage.removeItem(draftKey(visitId));
}

export function useConsultationDraftAutosave(
  visitId: string | undefined,
  draft: ConsultationDraft | null,
  enabled: boolean,
) {
  const draftRef = useRef(draft);
  draftRef.current = draft;

  useEffect(() => {
    if (!visitId || !enabled || !draft) return;

    const timer = window.setInterval(() => {
      if (!draftRef.current) return;
      saveConsultationDraft(visitId, {
        ...draftRef.current,
        savedAt: new Date().toISOString(),
      });
    }, DRAFT_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [visitId, enabled, draft]);
}
