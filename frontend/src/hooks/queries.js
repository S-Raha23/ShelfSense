// Data-fetching hooks. Query keys are hierarchical (["products", params]) so a single
// invalidateQueries({ queryKey: ["products"] }) refreshes every products view at once.
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { dashboardApi, productsApi, recommendationsApi, syncApi } from "../api/services";

export const useSummary = (days) =>
  useQuery({ queryKey: ["dashboard", "summary", days], queryFn: () => dashboardApi.summary(days) });

export const useTimeseries = (days, granularity) =>
  useQuery({
    queryKey: ["dashboard", "timeseries", days, granularity],
    queryFn: () => dashboardApi.timeseries(days, granularity),
  });

export const useTopProducts = (days) =>
  useQuery({ queryKey: ["dashboard", "top", days], queryFn: () => dashboardApi.topProducts(days) });

export const useProducts = (params) =>
  useQuery({
    queryKey: ["products", params],
    queryFn: () => productsApi.list(params),
    placeholderData: keepPreviousData, // keep the table on screen while the next page loads
  });

export const useProduct = (id, days) =>
  useQuery({ queryKey: ["products", "detail", id, days], queryFn: () => productsApi.get(id, days) });

export const useProductMetrics = (id, days) =>
  useQuery({ queryKey: ["products", "metrics", id, days], queryFn: () => productsApi.metrics(id, days) });

export const useRecommendations = (params) =>
  useQuery({
    queryKey: ["recommendations", params],
    queryFn: () => recommendationsApi.list(params),
    placeholderData: keepPreviousData,
  });

export const useRecommendationSummary = () =>
  useQuery({ queryKey: ["recommendations", "summary"], queryFn: recommendationsApi.summary });

export const useSyncJobs = (page) =>
  useQuery({ queryKey: ["sync", "jobs", page], queryFn: () => syncApi.jobs(page) });

/**
 * Mark a recommendation done / dismissed with an *optimistic update*: the card leaves the list
 * immediately, and is restored if the server rejects the change.
 */
export function useRecommendationAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action }) => recommendationsApi.act(id, action),
    onMutate: async ({ id }) => {
      await queryClient.cancelQueries({ queryKey: ["recommendations"] });
      const snapshot = queryClient.getQueriesData({ queryKey: ["recommendations"] });
      queryClient.setQueriesData({ queryKey: ["recommendations"] }, (old) =>
        old?.results ? { ...old, results: old.results.filter((r) => r.id !== id), count: old.count - 1 } : old,
      );
      return { snapshot };
    },
    onError: (_err, _vars, context) => {
      context?.snapshot.forEach(([key, value]) => queryClient.setQueryData(key, value));
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
}

/** Run a marketplace sync, then refresh everything that depends on synced data. */
export function useSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: syncApi.run,
    onSettled: () => {
      ["dashboard", "products", "recommendations", "sync"].forEach((key) =>
        queryClient.invalidateQueries({ queryKey: [key] }),
      );
    },
  });
}
