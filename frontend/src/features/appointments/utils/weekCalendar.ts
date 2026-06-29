/** Week calendar helpers — Sunday-start weeks (matches doctor schedule day_of_week). */

export interface WeekDay {
  date: Date;
  iso: string;
  label: string;
  shortLabel: string;
  isToday: boolean;
}

function toIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function startOfWeek(date: Date): Date {
  const value = new Date(date);
  value.setHours(0, 0, 0, 0);
  value.setDate(value.getDate() - value.getDay());
  return value;
}

export function endOfWeek(date: Date): Date {
  const value = startOfWeek(date);
  value.setDate(value.getDate() + 6);
  return value;
}

export function addDays(date: Date, days: number): Date {
  const value = new Date(date);
  value.setDate(value.getDate() + days);
  return value;
}

export function getWeekDays(anchor: Date): WeekDay[] {
  const start = startOfWeek(anchor);
  const todayIso = toIsoDate(new Date());

  return Array.from({ length: 7 }, (_, index) => {
    const date = addDays(start, index);
    const iso = toIsoDate(date);
    return {
      date,
      iso,
      label: date.toLocaleDateString(undefined, { weekday: "long" }),
      shortLabel: date.toLocaleDateString(undefined, { weekday: "short" }),
      isToday: iso === todayIso,
    };
  });
}

export function formatWeekRange(anchor: Date): string {
  const start = startOfWeek(anchor);
  const end = endOfWeek(anchor);
  const sameMonth = start.getMonth() === end.getMonth();
  const startLabel = start.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
  const endLabel = end.toLocaleDateString(undefined, {
    month: sameMonth ? undefined : "short",
    day: "numeric",
    year: "numeric",
  });
  return `${startLabel} – ${endLabel}`;
}

export function compareTimeStrings(a: string, b: string): number {
  return a.localeCompare(b);
}
