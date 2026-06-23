/**
 * Default post-login landing paths per IMPLEMENTATION_PLAN.md §3.3.
 * First matching role in priority order wins when a user has multiple roles.
 */
const ROLE_LANDING_PRIORITY: ReadonlyArray<{ role: string; path: string }> = [
  { role: "hospital_owner", path: "/dashboard" },
  { role: "hospital_admin", path: "/dashboard" },
  { role: "doctor", path: "/opd/queue" },
  { role: "receptionist", path: "/opd/queue" },
  { role: "nurse", path: "/ipd/admissions" },
  { role: "accountant", path: "/billing/collection" },
  { role: "pharmacist", path: "/pharmacy/queue" },
  { role: "lab_technician", path: "/lab/orders" },
];

const DEFAULT_LANDING_PATH = "/dashboard";

export function resolveRoleLandingPath(roles: string[]): string {
  const normalized = new Set(roles.map((role) => role.toLowerCase()));

  for (const entry of ROLE_LANDING_PRIORITY) {
    if (normalized.has(entry.role)) {
      return entry.path;
    }
  }

  return DEFAULT_LANDING_PATH;
}

/** Use a deep-link target when present; otherwise land by role. */
export function resolvePostAuthPath(from: string | undefined, roles: string[]): string {
  if (from && from !== "/" && from !== "/login" && from !== "/dashboard") {
    return from;
  }
  return resolveRoleLandingPath(roles);
}
