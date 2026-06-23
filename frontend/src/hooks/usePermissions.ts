import { useMemo } from "react";
import {
  hasAllPermissions,
  hasAnyPermission,
  hasPermission,
} from "@/lib/permissions";
import { useAuth } from "@/providers/AuthProvider";

export function usePermissions() {
  const { permissions, isLoading, user } = useAuth();

  return useMemo(
    () => ({
      permissions,
      isLoading,
      user,
      hasPermission: (required: string) => hasPermission(permissions, required),
      hasAnyPermission: (required: readonly string[]) =>
        hasAnyPermission(permissions, required),
      hasAllPermissions: (required: readonly string[]) =>
        hasAllPermissions(permissions, required),
    }),
    [isLoading, permissions, user],
  );
}
