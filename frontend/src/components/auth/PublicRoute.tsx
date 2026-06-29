import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { resolveRoleLandingPath } from "@/lib/role-landing";
import { useAuth } from "@/providers/AuthProvider";

interface PublicRouteProps {
  children: ReactNode;
}

/** Auth pages: redirect signed-in users to their role landing. */
export function PublicRoute({ children }: PublicRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted">
        <span className="inline-flex items-center gap-2">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-primary" />
          Loading session…
        </span>
      </div>
    );
  }

  if (isAuthenticated && user) {
    return <Navigate to={resolveRoleLandingPath(user.roles)} replace />;
  }

  return <>{children}</>;
}
