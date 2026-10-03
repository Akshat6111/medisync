import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, getToken, setToken, setUnauthorizedHandler, type AuthUser, type LoginResponse, type Role } from "./api";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { full_name: string; email: string; password: string; role?: Role }) => Promise<void>;
  logout: () => void;
  setUserFromStorage: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const USER_KEY = "medisync_user";

function loadUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

function saveUser(u: AuthUser | null) {
  if (typeof window === "undefined") return;
  if (u) window.localStorage.setItem(USER_KEY, JSON.stringify(u));
  else window.localStorage.removeItem(USER_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const t = getToken();
    setTokenState(t);
    const cached = loadUser();
    setUser(cached);
    if (t) {
      api.get<AuthUser>("/auth/me")
        .then((me) => {
          saveUser(me);
          setUser(me);
        })
        .catch(() => {})
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    saveUser(null);
    setTokenState(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout();
      if (typeof window !== "undefined") window.location.assign("/login");
    });
  }, [logout]);

  const login = useCallback(async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("grant_type", "password");
    form.set("username", email);
    form.set("password", password);
    const res = await api.postForm<LoginResponse>("/auth/login", form, false);
    setToken(res.access_token);
    setTokenState(res.access_token);
    try {
      const me = await api.get<AuthUser>("/auth/me");
      saveUser(me);
      setUser(me);
    } catch {
      const fallback: AuthUser = {
        id: "",
        email,
        full_name: email.split("@")[0],
        role: "PATIENT",
        created_at: new Date().toISOString(),
      };
      saveUser(fallback);
      setUser(fallback);
    }
  }, []);

  const register = useCallback(async (data: { full_name: string; email: string; password: string; role?: Role }) => {
    const created = await api.post<AuthUser>("/auth/register", { ...data, role: data.role ?? "PATIENT" });
    saveUser(created);
    setUser(created);
  }, []);

  const setUserFromStorage = useCallback(() => setUser(loadUser()), []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: !!token,
      isLoading,
      login,
      register,
      logout,
      setUserFromStorage,
    }),
    [user, token, isLoading, login, register, logout, setUserFromStorage],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
