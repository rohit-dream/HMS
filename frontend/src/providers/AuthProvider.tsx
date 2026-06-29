import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { clearAuthSession, setAccessToken, setTenantSlug } from "@/api/auth-session";
import {
  getMeRequest,
  loginRequest,
  logoutRequest,
  refreshRequest,
} from "@/api/endpoints/auth";
import type { LoginCredentials, MeResponse } from "@/api/types/auth";

export interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: MeResponse | null;
  permissions: string[];
  login: (credentials: LoginCredentials) => Promise<MeResponse>;
  activateSession: (accessToken: string, tenantSlug?: string) => Promise<MeResponse>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadSession = useCallback(async () => {
    try {
      const refreshed = await refreshRequest();
      setAccessToken(refreshed.access_token);
      const me = await getMeRequest();
      setUser(me);
    } catch {
      clearAuthSession();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    void (async () => {
      await loadSession();
      setIsLoading(false);
    })();
  }, [loadSession]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setTenantSlug(credentials.tenantSlug);
    const data = await loginRequest(credentials);
    setAccessToken(data.access_token);
    const me = await getMeRequest();
    setUser(me);
    return me;
  }, []);

  const activateSession = useCallback(async (token: string, slug?: string) => {
    if (slug) {
      setTenantSlug(slug);
    }
    setAccessToken(token);
    const me = await getMeRequest();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      clearAuthSession();
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: user !== null,
      isLoading,
      user,
      permissions: user?.permissions ?? [],
      login,
      activateSession,
      logout,
    }),
    [activateSession, isLoading, login, logout, user],
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
