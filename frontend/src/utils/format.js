const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const currencyCompact = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});
const number = new Intl.NumberFormat("en-US");

/** DRF serialises decimals as strings ("1234.50"); accept both strings and numbers. */
const toNumber = (value) => (value === null || value === undefined || value === "" ? null : Number(value));

export function formatCurrency(value, { compact = false } = {}) {
  const n = toNumber(value);
  if (n === null || Number.isNaN(n)) return "—";
  return compact && Math.abs(n) >= 10_000 ? currencyCompact.format(n) : currency.format(n);
}

/** Short labels for chart axes: $7.5K, $40, $0. */
export function formatCurrencyAxis(value) {
  const n = toNumber(value) ?? 0;
  return Math.abs(n) >= 1000 ? currencyCompact.format(n) : `$${Math.round(n * 100) / 100}`;
}

export function formatNumber(value) {
  const n = toNumber(value);
  return n === null || Number.isNaN(n) ? "—" : number.format(n);
}

export function formatPercent(value, digits = 1) {
  const n = toNumber(value);
  return n === null || Number.isNaN(n) ? "—" : `${n.toFixed(digits)}%`;
}

/** "+12.3%" / "-4.0%" for period-over-period changes. */
export function formatChange(value) {
  const n = toNumber(value);
  if (n === null || Number.isNaN(n)) return null;
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}

export function formatDate(value, options = { month: "short", day: "numeric" }) {
  if (!value) return "—";
  // Date-only strings ("2026-11-16") would otherwise be parsed as UTC midnight and can
  // shift a day in negative-offset timezones.
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T00:00:00`) : new Date(value);
  return date.toLocaleDateString("en-US", options);
}

export function formatDateTime(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export function timeAgo(value, now = Date.now()) {
  if (!value) return "never";
  const seconds = Math.round((now - new Date(value).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return `${Math.round(hours / 24)} d ago`;
}
