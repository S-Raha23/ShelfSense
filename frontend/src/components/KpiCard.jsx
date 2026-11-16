import { formatChange } from "../utils/format";

export default function KpiCard({ label, value, change, hint }) {
  const changeText = formatChange(change);
  const direction = change > 0 ? "up" : change < 0 ? "down" : "flat";
  return (
    <div className="card kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-foot">
        {changeText && <span className={`delta delta-${direction}`}>{changeText}</span>}
        {hint && <span className="muted">{hint}</span>}
      </div>
    </div>
  );
}
