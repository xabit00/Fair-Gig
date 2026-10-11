import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  api,
  getStoredSession,
  storeSession,
  subscribeToSession,
} from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(getStoredSession);
  const [loading, setLoading] = useState(true);

  useEffect(() => subscribeToSession(setSession), []);

  useEffect(() => {
    let active = true;
    async function restore() {
      const saved = getStoredSession();
      if (!saved) {
        if (active) setLoading(false);
        return;
      }
      try {
        const user = await api.get("auth", "/me");
        if (active) storeSession({ ...getStoredSession(), user });
      } catch (error) {
        if (error.status === 401) storeSession(null);
      } finally {
        if (active) setLoading(false);
      }
    }
    restore();
    return () => { active = false; };
  }, []);

  const authenticate = useCallback(async (path, payload) => {
    const nextSession = await api.post("auth", path, payload, { auth: false });
    storeSession(nextSession);
    return nextSession.user;
  }, []);

  const login = useCallback(
    (email, password) => authenticate("/login", { email, password }),
    [authenticate],
  );

  const register = useCallback(
    (payload) => authenticate("/register", payload),
    [authenticate],
  );

  const logout = useCallback(() => storeSession(null), []);

  const value = useMemo(() => ({
    user: session?.user || null,
    loading,
    login,
    register,
    logout,
    api,
  }), [loading, login, logout, register, session]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
