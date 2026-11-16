import { useState } from "react";
import { Link } from "react-router-dom";

import Icon from "../components/Icon";
import PeriodSelect from "../components/PeriodSelect";
import Spinner from "../components/Spinner";
import { EmptyState, ErrorState } from "../components/States";
import { useProducts } from "../hooks/queries";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { usePeriod } from "../hooks/usePeriod";
import { formatCurrency, formatNumber, formatPercent } from "../utils/format";

const SORTS = [
  { value: "-revenue_period", label: "Revenue (high → low)" },
  { value: "-units_period", label: "Units (high → low)" },
  { value: "inventory_qty", label: "Inventory (low → high)" },
  { value: "rating", label: "Rating (low → high)" },
  { value: "title", label: "Name (A → Z)" },
];

export default function ProductsPage() {
  const [days, setDays] = usePeriod();
  const [search, setSearch] = useState("");
  const [ordering, setOrdering] = useState(SORTS[0].value);
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search);

  // Filtering, sorting and pagination all happen server-side (DRF), so this scales
  // to catalogs far larger than one page.
  const { data, isLoading, isError, error, refetch, isFetching } = useProducts({
    days,
    search: debouncedSearch || undefined,
    ordering,
    page,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.count / 20)) : 1;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Products</h1>
          <p className="muted">{data ? `${data.count} listings` : " "}</p>
        </div>
        <PeriodSelect value={days} onChange={setDays} />
      </div>

      <div className="toolbar">
        <div className="input-icon">
          <Icon name="search" size={16} />
          <input
            placeholder="Search by title, ASIN or category"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <select value={ordering} onChange={(e) => setOrdering(e.target.value)} aria-label="Sort by">
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <Spinner />}
      {isError && <ErrorState error={error} onRetry={refetch} />}
      {data && data.results.length === 0 && <EmptyState title="No products match your search" />}
      {data && data.results.length > 0 && (
        <div className={`card table-card ${isFetching ? "is-refreshing" : ""}`}>
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th className="num">Price</th>
                  <th className="num">Rating</th>
                  <th className="num">Inventory</th>
                  <th className="num">Units</th>
                  <th className="num">Revenue</th>
                  <th className="num">Conv.</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.results.map((p) => {
                  const overpriced = p.competitor_price && Number(p.price) > Number(p.competitor_price) * 1.1;
                  return (
                    <tr key={p.id}>
                      <td>
                        <Link to={`/products/${p.id}?days=${days}`} className="cell-title">
                          {p.title}
                        </Link>
                        <div className="muted mono small">
                          {p.asin} · {p.category}
                        </div>
                      </td>
                      <td className="num">
                        {formatCurrency(p.price)}
                        {overpriced && <div className="small text-warn">vs {formatCurrency(p.competitor_price)}</div>}
                      </td>
                      <td className="num">{Number(p.rating).toFixed(1)}★</td>
                      <td className="num">{formatNumber(p.inventory_qty)}</td>
                      <td className="num">{formatNumber(p.units_period)}</td>
                      <td className="num">{formatCurrency(p.revenue_period)}</td>
                      <td className="num">{formatPercent(p.conversion_rate)}</td>
                      <td className="num">
                        {p.open_recommendations > 0 && (
                          <span className="badge badge-medium" title="Open recommendations">
                            {p.open_recommendations}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="pagination">
              <button className="btn btn-ghost btn-sm" disabled={!data.previous} onClick={() => setPage(page - 1)}>
                Previous
              </button>
              <span className="muted">
                Page {page} of {totalPages}
              </span>
              <button className="btn btn-ghost btn-sm" disabled={!data.next} onClick={() => setPage(page + 1)}>
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
