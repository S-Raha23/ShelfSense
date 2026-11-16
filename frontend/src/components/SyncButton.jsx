import { useEffect, useState } from "react";

import { errorMessage } from "../api/client";
import { useSync } from "../hooks/queries";
import Icon from "./Icon";

export default function SyncButton({ label = "Sync from Amazon", className = "" }) {
  const sync = useSync();
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(timer);
  }, [toast]);

  const run = () =>
    sync.mutate(undefined, {
      onSuccess: (job) =>
        setToast({
          kind: "success",
          text: `Synced ${job.products_upserted} products · ${job.recommendations_created} new, ${job.recommendations_updated} updated recommendations`,
        }),
      onError: (err) => {
        const job = err.response?.data;
        setToast({ kind: "error", text: job?.error ? `Sync failed: ${job.error}` : errorMessage(err) });
      },
    });

  return (
    <>
      <button className={`btn btn-primary ${className}`} onClick={run} disabled={sync.isPending}>
        <Icon name="sync" size={16} className={sync.isPending ? "spin" : ""} />
        {sync.isPending ? "Syncing…" : label}
      </button>
      {toast && (
        <div className={`toast toast-${toast.kind}`} role="status">
          <Icon name={toast.kind === "success" ? "check" : "alert"} size={16} />
          {toast.text}
        </div>
      )}
    </>
  );
}
