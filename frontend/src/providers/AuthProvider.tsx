import { createContext, useContext, useMemo, type ReactNode } from "react";

export interface AuthContextValue {
  isAuthenticated: boolean;
  user: null;
  permissions: string[];
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: false,
      user: null,
      permissions: [],
      login: async () => {
        /* Sprint 2 */
      },
      logout: async () => {
        /* Sprint 2 */
      },
    }),
    [],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
