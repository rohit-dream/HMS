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
      <div className="flex min-h-screen items-center justify-center bg-surface text-sm text-muted">
        Loading session…
      </div>
    );
  }

  if (isAuthenticated && user) {
    return <Navigate to={resolveRoleLandingPath(user.roles)} replace />;
  }

  return <>{children}</>;
}
