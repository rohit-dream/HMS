/**
 * Client-side permission checks — mirrors backend app/core/permissions.py.
 * UI only; API enforces authorization independently.
 */

export function hasPermission(
  userPermissions: readonly string[],
  required: string,
): boolean {
  const perms = new Set(userPermissions);
  if (perms.has("*:*")) {
    return true;
  }
  if (perms.has(required)) {
    return true;
  }
  const colon = required.indexOf(":");
  if (colon > 0) {
    const module = required.slice(0, colon);
    if (perms.has(`${module}:*`)) {
      return true;
    }
  }
  return false;
}

export function hasAnyPermission(
  userPermissions: readonly string[],
  required: readonly string[],
): boolean {
  return required.some((permission) => hasPermission(userPermissions, permission));
}

export function hasAllPermissions(
  userPermissions: readonly string[],
  required: readonly string[],
): boolean {
  return required.every((permission) => hasPermission(userPermissions, permission));
}
