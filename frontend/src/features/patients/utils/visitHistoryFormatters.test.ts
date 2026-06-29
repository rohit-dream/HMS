import { describe, expect, it } from "vitest";
import {
  isOpdVisitStatus,
  patientVisitStatusLabel,
  truncateText,
} from "./visitHistoryFormatters";

describe("visitHistoryFormatters", () => {
  it("labels known OPD visit statuses", () => {
    expect(patientVisitStatusLabel("in_consultation")).toBe("In consultation");
    expect(patientVisitStatusLabel("completed")).toBe("Completed");
  });

  it("falls back for unknown statuses", () => {
    expect(patientVisitStatusLabel("custom_status")).toBe("custom status");
  });

  it("detects typed OPD statuses", () => {
    expect(isOpdVisitStatus("waiting")).toBe(true);
    expect(isOpdVisitStatus("unknown")).toBe(false);
  });

  it("truncates long clinical text", () => {
    const longText = "A".repeat(90);
    expect(truncateText(longText, 20)).toBe(`${"A".repeat(19)}…`);
    expect(truncateText(null)).toBe("—");
  });
});
