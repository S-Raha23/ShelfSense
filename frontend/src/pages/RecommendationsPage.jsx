import { useState } from "react";

import RecommendationCard from "../components/RecommendationCard";
import Spinner from "../components/Spinner";
import { EmptyState, ErrorState } from "../components/States";
import { useRecommendationAction, useRecommendations, useRecommendationSummary } from "../hooks/queries";
import { errorMessage } from "../api/client";
import { formatCurrency } from "../utils/format";

const STATUSES = ["open", "done", "dismissed", "expired"];
const CATEGORIES = [
  { value: "", label: "All categories" },
  { value: "inventory", label: "Inventory" },
  { value: "pricing", label: "Pricing" },
  { value: "listing", label: "Listing" },
];

export default function RecommendationsPage() {
  const [status, setStatus] = useState("open");
  const [category, setCategory] = useState("");
  const summary = useRecommendationSummary();
  const list = useRecommendations({ status, category: category || undefined, page_size: 50 });
  const action = useRecommendationAction();

  const s = summary.data;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Recommendations</h1>
          <p className="muted">Ranked by severity, then by estimated monthly revenue at stake.</p>
        </div>
      </div>

      {s && (
        <section className="summary-strip card">
          <div>
            <div className="kpi-label">Open</div>
            <div className="kpi-value">{s.open_total}</div>
          </div>
          <div>
            <div className="kpi-label">High priority</div>
            <div className="kpi-value text-danger">{s.high}</div>
          </div>
          <div>
            <div className="kpi-label">Medium / Low</div>
            <div className="kpi-value">
              {s.medium} / {s.low}
            </div>
          </div>
          <div>
            <div className="kpi-label">Revenue at stake</div>
            <div className="kpi-value">{formatCurrency(s.total_estimated_impact, { compact: true })}</div>
          </div>
        </section>
      )}

      <div className="toolbar">
        <div className="segmented" role="tablist" aria-label="Status">
          {STATUSES.map((st) => (
            <button key={st} role="tab" aria-selected={status === st} className={status === st ? "is-active" : ""} onClick={() => setStatus(st)}>
              {st[0].toUpperCase() + st.slice(1)}
            </button>
          ))}
        </div>
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      {action.isError && <div className="alert alert-error">{errorMessage(action.error)}</div>}
      {list.isLoading && <Spinner />}
      {list.isError && <ErrorState error={list.error} onRetry={list.refetch} />}
      {list.data?.results.length === 0 && (
        <EmptyState title={status === "open" ? "You're all caught up" : `No ${status} recommendations`}>
          {status === "open" && "New recommendations appear here after each marketplace sync."}
        </EmptyState>
      )}
      <div className="rec-grid">
        {list.data?.results.map((rec) => (
          <RecommendationCard
            key={rec.id}
            rec={rec}
            busy={action.isPending}
            onAction={(id, act) => action.mutate({ id, action: act })}
          />
        ))}
      </div>
    </>
  );
}
