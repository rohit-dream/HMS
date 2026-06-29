import { describe, expect, it } from "vitest";
import { endOfWeek, formatWeekRange, getWeekDays, startOfWeek } from "./weekCalendar";

function toIso(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

describe("weekCalendar", () => {
  it("starts the week on Sunday", () => {
    const anchor = new Date(2026, 5, 25);
    const start = startOfWeek(anchor);
    expect(start.getDay()).toBe(0);
    expect(toIso(start)).toBe("2026-06-21");
  });

  it("ends the week on Saturday", () => {
    const anchor = new Date(2026, 5, 25);
    const end = endOfWeek(anchor);
    expect(end.getDay()).toBe(6);
    expect(toIso(end)).toBe("2026-06-27");
  });

  it("returns seven consecutive days", () => {
    const days = getWeekDays(new Date(2026, 5, 25));
    expect(days).toHaveLength(7);
    expect(days[0]?.iso).toBe("2026-06-21");
    expect(days[6]?.iso).toBe("2026-06-27");
  });

  it("formats a readable week range", () => {
    const label = formatWeekRange(new Date(2026, 5, 25));
    expect(label).toContain("Jun");
    expect(label).toContain("27");
  });
});
