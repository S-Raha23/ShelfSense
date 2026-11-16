import { describe, expect, it } from "vitest";

import { formatChange, formatCurrency, formatDate, formatNumber, formatPercent, timeAgo } from "./format";

describe("format helpers", () => {
  it("formats DRF decimal strings as currency", () => {
    expect(formatCurrency("1234.5")).toBe("$1,234.50");
    expect(formatCurrency(227335.07, { compact: true })).toBe("$227.3K");
    expect(formatCurrency(null)).toBe("—");
  });

  it("formats numbers and percentages", () => {
    expect(formatNumber(8793)).toBe("8,793");
    expect(formatPercent(10.456)).toBe("10.5%");
  });

  it("signs period-over-period changes", () => {
    expect(formatChange(11.7)).toBe("+11.7%");
    expect(formatChange(-4)).toBe("-4.0%");
    expect(formatChange(null)).toBeNull();
  });

  it("does not shift date-only strings across timezones", () => {
    expect(formatDate("2026-11-01")).toBe("Nov 1");
  });

  it("renders relative times", () => {
    const now = new Date("2026-11-17T12:00:00Z").getTime();
    expect(timeAgo("2026-11-17T11:58:00Z", now)).toBe("2 min ago");
    expect(timeAgo(null)).toBe("never");
  });
});
