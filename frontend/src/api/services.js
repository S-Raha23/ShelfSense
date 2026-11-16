// One function per backend endpoint. Components never build URLs themselves.
import { api } from "./client";

const data = (promise) => promise.then((res) => res.data);

export const authApi = {
  login: (credentials) => data(api.post("/auth/token/", credentials)),
  register: (payload) => data(api.post("/auth/register/", payload)),
  me: () => data(api.get("/auth/me/")),
};

export const dashboardApi = {
  summary: (days) => data(api.get("/dashboard/summary/", { params: { days } })),
  timeseries: (days, granularity) => data(api.get("/dashboard/timeseries/", { params: { days, granularity } })),
  topProducts: (days, limit = 5) => data(api.get("/dashboard/top-products/", { params: { days, limit } })),
};

export const productsApi = {
  list: (params) => data(api.get("/products/", { params })),
  get: (id, days) => data(api.get(`/products/${id}/`, { params: { days } })),
  metrics: (id, days) => data(api.get(`/products/${id}/metrics/`, { params: { days } })),
};

export const recommendationsApi = {
  list: (params) => data(api.get("/recommendations/", { params })),
  summary: () => data(api.get("/recommendations/summary/")),
  act: (id, action) => data(api.post(`/recommendations/${id}/${action}/`)),
};

export const syncApi = {
  run: () => data(api.post("/sync/")),
  jobs: (page = 1) => data(api.get("/sync/jobs/", { params: { page } })),
};
