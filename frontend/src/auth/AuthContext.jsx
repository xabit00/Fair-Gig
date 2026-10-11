import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

const AUTH_API = import.meta.env.VITE_AUTH_API_URL || "http://localhost:8001";
const STORAGE_KEY = "fairgig.session";
const AuthContext = createContext(null);

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "The request could not be completed.");
  }
  return data;
}

export function AuthProvider({ children }) {
  const [session, setSessionState] = useState(null);
  const [loading, setLoading] = useState(true);
  const sessionRef = useRef(null);

  const saveSession = useCallback((nextSession) => {
    sessionRef.current = nextSession;
    setSessionState(nextSession);
    if (nextSession) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const refresh = useCallback(async (refreshToken) => {
    const token = refreshToken || sessionRef.current?.refresh_token;
    if (!token) throw new Error("Your session has ended. Please sign in again.");
    const response = await fetch(`${AUTH_API}/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token }),
    });
    const nextSession = await parseResponse(response);
    saveSession(nextSession);
    return nextSession;
  }, [saveSession]);

  useEffect(() => {
    async function restore() {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        setLoading(false);
        return;
      }
      try {
        const savedSession = JSON.parse(stored);
        sessionRef.current = savedSession;
        const response = await fetch(`${AUTH_API}/me`, {
          headers: { Authorization: `Bearer ${savedSession.access_token}` },
        });
        if (response.ok) {
          const user = await response.json();
          saveSession({ ...savedSession, user });
        } else {
          await refresh(savedSession.refresh_token);
        }
      } catch (_error) {
        saveSession(null);
      } finally {
        setLoading(false);
      }
    }
    restore();
  }, [refresh, saveSession]);

  const authenticate = useCallback(async (path, payload) => {
    const response = await fetch(`${AUTH_API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const nextSession = await parseResponse(response);
    saveSession(nextSession);
    return nextSession.user;
  }, [saveSession]);

  const login = useCallback(
    (email, password) => authenticate("/login", { email, password }),
    [authenticate],
  );

  const register = useCallback(
    (payload) => authenticate("/register", payload),
    [authenticate],
  );

  const apiFetch = useCallback(async (url, options = {}) => {
    let activeSession = sessionRef.current;
    if (!activeSession) throw new Error("Authentication required.");
    const request = (accessToken) => fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${accessToken}`,
      },
    });
    let response = await request(activeSession.access_token);
    if (response.status === 401) {
      activeSession = await refresh(activeSession.refresh_token);
      response = await request(activeSession.access_token);
    }
    return response;
  }, [refresh]);

  const value = useMemo(() => ({
    user: session?.user || null,
    loading,
    login,
    register,
    refresh,
    apiFetch,
    logout: () => saveSession(null),
  }), [apiFetch, loading, login, refresh, register, saveSession, session]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

