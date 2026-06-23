import type { ReactNode } from "react";
import { usePermissions } from "@/hooks/usePermissions";

interface PermissionGuardBaseProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface PermissionGuardSingleProps extends PermissionGuardBaseProps {
  permission: string;
  anyOf?: never;
  allOf?: never;
}

interface PermissionGuardAnyProps extends PermissionGuardBaseProps {
  permission?: never;
  anyOf: readonly string[];
  allOf?: never;
}

interface PermissionGuardAllProps extends PermissionGuardBaseProps {
  permission?: never;
  anyOf?: never;
  allOf: readonly string[];
}

export type PermissionGuardProps =
  | PermissionGuardSingleProps
  | PermissionGuardAnyProps
  | PermissionGuardAllProps;

/** Renders children only when the current user has the required permission(s). */
export function PermissionGuard({
  children,
  fallback = null,
  permission,
  anyOf,
  allOf,
}: PermissionGuardProps) {
  const { hasPermission, hasAnyPermission, hasAllPermissions, isLoading } =
    usePermissions();

  if (isLoading) {
    return null;
  }

  let allowed = false;
  if (permission) {
    allowed = hasPermission(permission);
  } else if (anyOf) {
    allowed = hasAnyPermission(anyOf);
  } else if (allOf) {
    allowed = hasAllPermissions(allOf);
  }

  return allowed ? <>{children}</> : <>{fallback}</>;
}
