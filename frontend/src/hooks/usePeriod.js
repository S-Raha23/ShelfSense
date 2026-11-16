import { useSearchParams } from "react-router-dom";

export const PERIOD_OPTIONS = [7, 30, 60, 90];

/**
 * The selected date range lives in the URL (?days=30) rather than component state, so a view
 * can be bookmarked or shared and survives a page refresh.
 */
export function usePeriod(defaultDays = 30) {
  const [params, setParams] = useSearchParams();
  const raw = Number(params.get("days"));
  const days = PERIOD_OPTIONS.includes(raw) ? raw : defaultDays;

  const setDays = (value) => {
    const next = new URLSearchParams(params);
    next.set("days", String(value));
    setParams(next, { replace: true });
  };
  return [days, setDays];
}
