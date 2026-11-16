import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { tokenStore } from "../api/client";
import { authApi } from "../api/services";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState(tokenStore.access ? "loading" : "anonymous");

  const logout = useCallback(() => {
    tokenStore.clear();
    queryClient.clear(); // never show the previous user's cached data to the next one
    setUser(null);
    setStatus("anonymous");
  }, [queryClient]);

  // Restore the session on page load if we still hold a token.
  useEffect(() => {
    if (!tokenStore.access) return;
    authApi
      .me()
      .then((me) => {
        setUser(me);
        setStatus("authenticated");
      })
      .catch(logout);
  }, [logout]);

  // The axios interceptor fires this when the refresh token itself has expired.
  useEffect(() => {
    window.addEventListener("auth:expired", logout);
    return () => window.removeEventListener("auth:expired", logout);
  }, [logout]);

  const login = useCallback(async (username, password) => {
    tokenStore.set(await authApi.login({ username, password }));
    const me = await authApi.me();
    setUser(me);
    setStatus("authenticated");
  }, []);

  const register = useCallback(async (payload) => {
    const { user: me, access, refresh } = await authApi.register(payload);
    tokenStore.set({ access, refresh });
    setUser(me);
    setStatus("authenticated");
  }, []);

  const value = useMemo(() => ({ user, status, login, register, logout }), [user, status, login, register, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
