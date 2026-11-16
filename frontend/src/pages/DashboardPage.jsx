import { Link } from "react-router-dom";

import KpiCard from "../components/KpiCard";
import PeriodSelect from "../components/PeriodSelect";
import RecommendationCard from "../components/RecommendationCard";
import SalesChart from "../components/SalesChart";
import Spinner from "../components/Spinner";
import { EmptyState, ErrorState } from "../components/States";
import SyncButton from "../components/SyncButton";
import { useRecommendations, useRecommendationSummary, useSummary, useTimeseries, useTopProducts } from "../hooks/queries";
import { usePeriod } from "../hooks/usePeriod";
import { formatCurrency, formatDate, formatNumber, formatPercent } from "../utils/format";

export default function DashboardPage() {
  const [days, setDays] = usePeriod();
  const summary = useSummary(days);
  const series = useTimeseries(days, days > 60 ? "week" : "day");
  const top = useTopProducts(days);
  const recSummary = useRecommendationSummary();
  const recs = useRecommendations({ status: "open", page_size: 3 });

  if (summary.isLoading) return <Spinner />;
  if (summary.isError) return <ErrorState error={summary.error} onRetry={summary.refetch} />;

  const s = summary.data;
  if (s.active_products === 0) {
    return (
      <EmptyState title="No marketplace data yet" action={<SyncButton label="Run your first sync" />}>
        Sync your Amazon catalog to see sales trends and get recommendations.
      </EmptyState>
    );
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">
            {formatDate(s.period.start)} – {formatDate(s.period.end)} · compared with the previous {days} days
          </p>
        </div>
        <PeriodSelect value={days} onChange={setDays} />
      </div>

      <section className="kpi-grid">
        <KpiCard label="Revenue" value={formatCurrency(s.revenue, { compact: true })} change={s.change.revenue} />
        <KpiCard label="Units sold" value={formatNumber(s.units)} change={s.change.units} />
        <KpiCard label="Conversion rate" value={formatPercent(s.conversion_rate)} change={s.change.conversion_rate} />
        <KpiCard
          label="Revenue at stake"
          value={formatCurrency(recSummary.data?.total_estimated_impact, { compact: true })}
          hint={`${recSummary.data?.open_total ?? 0} open recommendations`}
        />
      </section>

      <section className="card">
        <div className="card-head">
          <h2>Sales trend</h2>
          <span className="muted">{days > 60 ? "Weekly" : "Daily"}</span>
        </div>
        {series.isLoading ? <Spinner /> : <SalesChart data={series.data} />}
      </section>

      <div className="grid-2">
        <section className="card">
          <div className="card-head">
            <h2>Top products</h2>
            <Link to={`/products?days=${days}`}>View all</Link>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th className="num">Units</th>
                <th className="num">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {top.data?.map((p) => (
                <tr key={p.id}>
                  <td>
                    <Link to={`/products/${p.id}?days=${days}`} className="cell-title">
                      {p.title}
                    </Link>
                  </td>
                  <td className="num">{formatNumber(p.units_period)}</td>
                  <td className="num">{formatCurrency(p.revenue_period)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card">
          <div className="card-head">
            <h2>Do this next</h2>
            <Link to="/recommendations">All recommendations</Link>
          </div>
          <div className="stack">
            {recs.data?.results.map((rec) => <RecommendationCard key={rec.id} rec={rec} compact />)}
            {recs.data?.results.length === 0 && <p className="muted">Nothing urgent. Nice work.</p>}
          </div>
        </section>
      </div>
    </>
  );
}
