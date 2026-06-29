import { AlertTriangle } from "lucide-react";
import type { DuplicatePatientMatch } from "@/api/types/patients";
import { Alert } from "@/components/ui/Alert";
import { formatDate, formatPatientName, formatPhone } from "@/lib/formatters";

interface DuplicatePatientAlertProps {
  matches: DuplicatePatientMatch[];
  acknowledged: boolean;
  onAcknowledgeChange: (value: boolean) => void;
  acknowledgeError?: string;
}

function reasonLabel(reason: string): string {
  if (reason === "phone") return "Phone";
  if (reason === "name") return "Name";
  return reason;
}

export function DuplicatePatientAlert({
  matches,
  acknowledged,
  onAcknowledgeChange,
  acknowledgeError,
}: DuplicatePatientAlertProps) {
  if (matches.length === 0) return null;

  return (
    <Alert variant="warning" className="space-y-3">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        <div className="space-y-2">
          <p className="font-medium">Possible duplicate patient found</p>
          <p className="text-sm opacity-90">
            Review the matches below. You may still register if this is a different person or a
            shared family phone number.
          </p>
          <ul className="space-y-2 text-sm">
            {matches.map((match) => (
              <li
                key={match.patient_id}
                className="rounded-md border border-amber-200/80 bg-white/60 px-3 py-2"
              >
                <div className="font-medium text-foreground">
                  {formatPatientName(match.first_name, match.last_name)}
                </div>
                <div className="mt-1 text-muted">
                  MRN {match.mrn} · {formatPhone(match.phone)} · DOB {formatDate(match.date_of_birth)}
                </div>
                <div className="mt-1 text-xs text-muted">
                  Matched on: {match.match_reasons.map(reasonLabel).join(", ")}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <label className="flex items-start gap-2 text-sm">
        <input
          type="checkbox"
          className="mt-1"
          checked={acknowledged}
          onChange={(event) => onAcknowledgeChange(event.target.checked)}
        />
        <span>I have reviewed the possible duplicates and want to proceed with registration.</span>
      </label>
      {acknowledgeError && <p className="text-xs text-error">{acknowledgeError}</p>}
    </Alert>
  );
}
