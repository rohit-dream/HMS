import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { usePermissions } from "@/hooks/usePermissions";

interface PermissionRouteBaseProps {
  children: ReactNode;
}

interface PermissionRouteSingleProps extends PermissionRouteBaseProps {
  permission: string;
  anyOf?: never;
  allOf?: never;
}

interface PermissionRouteAnyProps extends PermissionRouteBaseProps {
  permission?: never;
  anyOf: readonly string[];
  allOf?: never;
}

interface PermissionRouteAllProps extends PermissionRouteBaseProps {
  permission?: never;
  anyOf?: never;
  allOf: readonly string[];
}

export type PermissionRouteProps =
  | PermissionRouteSingleProps
  | PermissionRouteAnyProps
  | PermissionRouteAllProps;

/** Blocks route access when the user lacks required permission(s). */
export function PermissionRoute({
  children,
  permission,
  anyOf,
  allOf,
}: PermissionRouteProps) {
  const { hasPermission, hasAnyPermission, hasAllPermissions, isLoading } =
    usePermissions();

  if (isLoading) {
    return (
      <div className="flex min-h-[12rem] items-center justify-center text-sm text-muted">
        Loading permissions…
      </div>
    );
  }

  let allowed = false;
  if (permission) {
    allowed = hasPermission(permission);
  } else if (anyOf) {
    allowed = hasAnyPermission(anyOf);
  } else if (allOf) {
    allowed = hasAllPermissions(allOf);
  }

  if (!allowed) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
