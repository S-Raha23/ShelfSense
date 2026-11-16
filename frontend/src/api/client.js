import axios from "axios";

// Same-origin "/api" by default (nginx / Vite proxy). Set VITE_API_URL only when the API
// is hosted on a different domain.
export const API_URL = import.meta.env.VITE_API_URL || "/api";

const ACCESS_KEY = "shelfsense.access";
const REFRESH_KEY = "shelfsense.refresh";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const api = axios.create({ baseURL: API_URL, timeout: 20_000 });

api.interceptors.request.use((config) => {
  const token = tokenStore.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Access tokens live 15 minutes. When one expires, transparently refresh it and replay the
// request. `refreshPromise` makes concurrent 401s share a single refresh call instead of
// firing one per failed request (which would also break refresh-token rotation).
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const isAuthCall = original?.url?.includes("/auth/token");
    if (error.response?.status !== 401 || !original || original._retried || isAuthCall || !tokenStore.refresh) {
      throw error;
    }
    original._retried = true;
    try {
      refreshPromise ??= axios
        .post(`${API_URL}/auth/token/refresh/`, { refresh: tokenStore.refresh })
        .then(({ data }) => {
          tokenStore.set(data);
          return data.access;
        })
        .finally(() => {
          refreshPromise = null;
        });
      const access = await refreshPromise;
      original.headers.Authorization = `Bearer ${access}`;
      return api(original);
    } catch {
      tokenStore.clear();
      window.dispatchEvent(new Event("auth:expired"));
      throw error;
    }
  },
);

/** Turn a DRF error response into one human-readable message. */
export function errorMessage(error, fallback = "Something went wrong. Please try again.") {
  const data = error?.response?.data;
  if (!data) return error?.message === "Network Error" ? "Cannot reach the server." : fallback;
  if (typeof data === "string") return fallback;
  if (data.detail) return data.detail;
  const [field, messages] = Object.entries(data)[0] ?? [];
  if (!field) return fallback;
  const text = Array.isArray(messages) ? messages[0] : String(messages);
  return field === "non_field_errors" ? text : `${field.replace(/_/g, " ")}: ${text}`;
}
