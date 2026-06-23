import { Navigate } from "react-router-dom";
import { resolveRoleLandingPath } from "@/lib/role-landing";
import { useAuth } from "@/providers/AuthProvider";

/** Sends authenticated users to the default route for their primary role. */
export function RoleRedirect() {
  const { user, isLoading } = useAuth();

  if (isLoading || !user) {
    return (
      <div className="flex min-h-[12rem] items-center justify-center text-sm text-muted">
        Loading…
      </div>
    );
  }

  return <Navigate to={resolveRoleLandingPath(user.roles)} replace />;
}
