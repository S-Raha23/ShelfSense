import { Link } from "react-router-dom";

import { formatCurrency } from "../utils/format";
import Icon from "./Icon";

const CATEGORY_LABELS = { inventory: "Inventory", pricing: "Pricing", listing: "Listing" };

export function SeverityBadge({ severity, label }) {
  const level = { 3: "high", 2: "medium", 1: "low" }[severity];
  return <span className={`badge badge-${level}`}>{label}</span>;
}

export default function RecommendationCard({ rec, onAction, busy, compact = false }) {
  return (
    <article className={`card rec rec-sev-${rec.severity}`}>
      <div className="rec-head">
        <SeverityBadge severity={rec.severity} label={rec.severity_label} />
        <span className="chip">{CATEGORY_LABELS[rec.category] ?? rec.category}</span>
        <span className="rec-impact" title="Estimated monthly revenue at stake">
          {formatCurrency(rec.estimated_impact, { compact: true })}
          <small>/mo at stake</small>
        </span>
      </div>
      <h3 className="rec-title">{rec.title}</h3>
      {!compact && <p className="rec-message">{rec.message}</p>}
      <div className="rec-foot">
        <Link to={`/products/${rec.product.id}`} className="muted mono">
          {rec.product.asin}
        </Link>
        {onAction && rec.status === "open" && (
          <div className="rec-actions">
            <button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => onAction(rec.id, "dismiss")}>
              <Icon name="x" size={14} /> Dismiss
            </button>
            <button className="btn btn-success btn-sm" disabled={busy} onClick={() => onAction(rec.id, "complete")}>
              <Icon name="check" size={14} /> Mark done
            </button>
          </div>
        )}
        {rec.status !== "open" && <span className={`chip chip-${rec.status}`}>{rec.status}</span>}
      </div>
    </article>
  );
}
