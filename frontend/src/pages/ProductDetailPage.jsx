import { Link, useParams } from "react-router-dom";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import Icon from "../components/Icon";
import KpiCard from "../components/KpiCard";
import PeriodSelect from "../components/PeriodSelect";
import RecommendationCard from "../components/RecommendationCard";
import SalesChart from "../components/SalesChart";
import Spinner from "../components/Spinner";
import { ErrorState } from "../components/States";
import { useProduct, useProductMetrics, useRecommendationAction, useRecommendations } from "../hooks/queries";
import { usePeriod } from "../hooks/usePeriod";
import { formatCurrency, formatCurrencyAxis, formatDate, formatNumber, formatPercent, timeAgo } from "../utils/format";

export default function ProductDetailPage() {
  const { id } = useParams();
  const [days, setDays] = usePeriod();
  const product = useProduct(id, days);
  const metrics = useProductMetrics(id, days);
  const recs = useRecommendations({ product: id, status: "open" });
  const action = useRecommendationAction();

  if (product.isLoading) return <Spinner />;
  if (product.isError) return <ErrorState error={product.error} />;

  const p = product.data;
  const series = (metrics.data ?? []).map((m) => ({
    ...m,
    price: Number(m.price),
    competitor_price: m.competitor_price ? Number(m.competitor_price) : null,
  }));

  return (
    <>
      <Link to={`/products?days=${days}`} className="back-link">
        <Icon name="arrowLeft" size={16} /> Products
      </Link>
      <div className="page-head">
        <div>
          <h1>{p.title}</h1>
          <p className="muted">
            <span className="mono">{p.asin}</span> · {p.category} · synced {timeAgo(p.last_synced_at)}
          </p>
        </div>
        <PeriodSelect value={days} onChange={setDays} />
      </div>

      <section className="kpi-grid">
        <KpiCard label={`Revenue (${days}d)`} value={formatCurrency(p.revenue_period)} />
        <KpiCard label="Units" value={formatNumber(p.units_period)} hint={`${formatNumber(p.sessions_period)} sessions`} />
        <KpiCard label="Conversion" value={formatPercent(p.conversion_rate)} />
        <KpiCard
          label="Price"
          value={formatCurrency(p.price)}
          hint={p.competitor_price ? `Competitor ${formatCurrency(p.competitor_price)}` : null}
        />
        <KpiCard label="Rating" value={`${Number(p.rating).toFixed(2)}★`} hint={`${formatNumber(p.review_count)} reviews`} />
        <KpiCard label="Inventory" value={formatNumber(p.inventory_qty)} hint="units on hand" />
      </section>

      {recs.data?.results.length > 0 && (
        <section className="stack">
          <h2>Recommendations</h2>
          {recs.data.results.map((rec) => (
            <RecommendationCard
              key={rec.id}
              rec={rec}
              busy={action.isPending}
              onAction={(recId, act) => action.mutate({ id: recId, action: act })}
            />
          ))}
        </section>
      )}

      <section className="card">
        <div className="card-head">
          <h2>Sales</h2>
        </div>
        {metrics.isLoading ? <Spinner /> : <SalesChart data={metrics.data} height={260} />}
      </section>

      <div className="grid-2">
        <section className="card">
          <div className="card-head">
            <h2>Price vs competitor</h2>
          </div>
          <MiniLineChart
            data={series}
            lines={[
              { key: "price", name: "Your price", color: "var(--accent)" },
              { key: "competitor_price", name: "Competitor", color: "var(--muted)" },
            ]}
            format={formatCurrencyAxis}
          />
        </section>
        <section className="card">
          <div className="card-head">
            <h2>Rating & inventory</h2>
          </div>
          <MiniLineChart
            data={series.map((m) => ({ ...m, rating: Number(m.rating) }))}
            lines={[{ key: "inventory_qty", name: "Inventory", color: "var(--info)" }]}
            secondary={{ key: "rating", name: "Rating", color: "var(--warn)", domain: [3, 5] }}
            format={formatNumber}
          />
        </section>
      </div>
    </>
  );
}

function MiniLineChart({ data, lines, secondary, format }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="date" tickFormatter={(v) => formatDate(v)} tick={{ fontSize: 12 }} stroke="var(--muted)" minTickGap={24} />
        <YAxis yAxisId="left" tickFormatter={format} tick={{ fontSize: 12 }} stroke="var(--muted)" width={60} domain={["auto", "auto"]} />
        {secondary && (
          <YAxis yAxisId="right" orientation="right" domain={secondary.domain} tick={{ fontSize: 12 }} stroke="var(--muted)" width={32} />
        )}
        <Tooltip labelFormatter={(v) => formatDate(v)} contentStyle={{ borderRadius: 8, border: "1px solid var(--border)" }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {lines.map((l) => (
          <Line key={l.key} yAxisId="left" dataKey={l.key} name={l.name} stroke={l.color} strokeWidth={2} dot={false} />
        ))}
        {secondary && (
          <Line yAxisId="right" dataKey={secondary.key} name={secondary.name} stroke={secondary.color} strokeWidth={2} dot={false} />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
