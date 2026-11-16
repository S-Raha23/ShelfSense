import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatCurrency, formatCurrencyAxis, formatDate, formatNumber } from "../utils/format";

const METRICS = {
  revenue: { label: "Revenue", format: formatCurrencyAxis },
  units: { label: "Units", format: formatNumber },
  sessions: { label: "Sessions", format: formatNumber },
};

export default function SalesChart({ data = [], height = 300 }) {
  const [metric, setMetric] = useState("revenue");
  const { format } = METRICS[metric];
  const points = data.map((d) => ({ ...d, [metric]: Number(d[metric]) }));

  return (
    <div>
      <div className="segmented" role="tablist" aria-label="Chart metric">
        {Object.entries(METRICS).map(([key, { label }]) => (
          <button
            key={key}
            role="tab"
            aria-selected={metric === key}
            className={metric === key ? "is-active" : ""}
            onClick={() => setMetric(key)}
          >
            {label}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={points} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis dataKey="date" tickFormatter={(v) => formatDate(v)} tick={{ fontSize: 12 }} stroke="var(--muted)" minTickGap={24} />
          <YAxis tickFormatter={format} tick={{ fontSize: 12 }} stroke="var(--muted)" width={64} />
          <Tooltip
            formatter={(v) => [metric === "revenue" ? formatCurrency(v) : formatNumber(v), METRICS[metric].label]}
            labelFormatter={(v) => formatDate(v, { weekday: "short", month: "short", day: "numeric" })}
            contentStyle={{ borderRadius: 8, border: "1px solid var(--border)" }}
          />
          <Area type="monotone" dataKey={metric} stroke="var(--accent)" strokeWidth={2} fill="url(#salesFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
