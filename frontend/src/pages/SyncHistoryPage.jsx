import { useState } from "react";

import Spinner from "../components/Spinner";
import { EmptyState, ErrorState } from "../components/States";
import SyncButton from "../components/SyncButton";
import { useSyncJobs } from "../hooks/queries";
import { formatDateTime, formatNumber } from "../utils/format";

export default function SyncHistoryPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useSyncJobs(page);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Sync history</h1>
          <p className="muted">Every pull from the marketplace API, with what changed and any errors.</p>
        </div>
        <SyncButton label="Sync now" />
      </div>

      {isLoading && <Spinner />}
      {isError && <ErrorState error={error} onRetry={refetch} />}
      {data?.results.length === 0 && <EmptyState title="No syncs yet" />}
      {data?.results.length > 0 && (
        <div className="card table-card">
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Started</th>
                  <th>Status</th>
                  <th>Source</th>
                  <th className="num">Duration</th>
                  <th className="num">Products</th>
                  <th className="num">Metric rows</th>
                  <th className="num">Recs new / updated / expired</th>
                  <th>By</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((job) => (
                  <tr key={job.id}>
                    <td>{formatDateTime(job.started_at)}</td>
                    <td>
                      <span className={`chip chip-${job.status}`}>{job.status}</span>
                      {job.error && <div className="small text-danger">{job.error}</div>}
                    </td>
                    <td className="mono">{job.source}</td>
                    <td className="num">{job.duration_ms != null ? `${job.duration_ms} ms` : "—"}</td>
                    <td className="num">{formatNumber(job.products_upserted)}</td>
                    <td className="num">{formatNumber(job.metrics_upserted)}</td>
                    <td className="num">
                      {job.recommendations_created} / {job.recommendations_updated} / {job.recommendations_expired}
                    </td>
                    <td>{job.triggered_by ?? "system"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(data.next || data.previous) && (
            <div className="pagination">
              <button className="btn btn-ghost btn-sm" disabled={!data.previous} onClick={() => setPage(page - 1)}>
                Previous
              </button>
              <span className="muted">Page {page}</span>
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
