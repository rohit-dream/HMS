import { Navigate } from "react-router-dom";
import { resolveRoleLandingPath } from "@/lib/role-landing";
import { useAuth } from "@/providers/AuthProvider";
import { HomePage } from "@/pages/HomePage";

/**
 * Role router at /dashboard: admins see the dashboard shell;
 * clinical roles are forwarded to their module landing placeholders.
 */
export function DashboardPage() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  const landing = resolveRoleLandingPath(user.roles);
  if (landing !== "/dashboard") {
    return <Navigate to={landing} replace />;
  }

  return <HomePage />;
}
