# API reference

Base path: `/api`. Interactive docs (Swagger UI): **`/api/docs/`**. OpenAPI schema: `/api/schema/`.

All endpoints except login, register and health require `Authorization: Bearer <access token>`.
Responses are JSON. Every list endpoint is paginated:

```json
{ "count": 12, "next": null, "previous": null, "results": [ ... ] }
```

Pagination uses `?page=` and `?page_size=` (max 100).

## Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register/` | Create a user and their brand. Returns the user and a token pair. |
| POST | `/auth/token/` | Log in with `{username, password}` and get `{access, refresh}` |
| POST | `/auth/token/refresh/` | `{refresh}` returns a new `{access, refresh}` (rotation) |
| GET | `/auth/me/` | Current user with brand and role |

```bash
curl -X POST /api/auth/register/ -H "Content-Type: application/json" \
  -d '{"username":"carol","password":"Str0ng-pass-99","brand_name":"Gamma Home"}'
```

Access tokens expire after 15 minutes and refresh tokens after 1 day. Login and register are throttled
(30/min).

## Dashboard

Shared query parameter: `days`, the period ending today (7–90, default 30).

| Method | Path | Extra params | Description |
|---|---|---|---|
| GET | `/dashboard/summary/` | | KPIs and % change versus the previous period |
| GET | `/dashboard/timeseries/` | `granularity=day\|week` | Revenue, units and sessions per bucket |
| GET | `/dashboard/top-products/` | `limit` (1–20) | Products by revenue in the period |

```json
// GET /api/dashboard/summary/?days=30
{
  "period": { "start": "2026-10-18", "end": "2026-11-16" },
  "revenue": "227335.07",
  "units": 8793,
  "sessions": 83712,
  "conversion_rate": 10.5,
  "avg_selling_price": 25.85,
  "change": { "revenue": 11.7, "units": 11.3, "sessions": 11.1, "conversion_rate": 0.2 },
  "active_products": 12
}
```

## Products (read-only, maintained by the sync)

| Method | Path | Description |
|---|---|---|
| GET | `/products/` | List with period stats. `search` (title/ASIN/category), `ordering` (`-revenue_period`, `units_period`, `inventory_qty`, `rating`, `price`, `title`), `category`, `is_active`, `days` |
| GET | `/products/{id}/` | One product with period stats |
| GET | `/products/{id}/metrics/` | Daily history for the period (`days`) |

```json
// GET /api/products/?ordering=-revenue_period&days=30  (one item)
{
  "id": 1, "asin": "B05597C179", "title": "Stainless Steel Insulated Water Bottle 32oz",
  "category": "Kitchen & Dining", "price": "24.99", "competitor_price": "24.26",
  "rating": "4.60", "review_count": 2847, "inventory_qty": 1824, "is_active": true,
  "last_synced_at": "2026-11-16T20:13:41Z",
  "units_period": 1424, "revenue_period": "35585.76", "sessions_period": 11931,
  "conversion_rate": 11.94, "open_recommendations": 0
}
```

## Recommendations

| Method | Path | Description |
|---|---|---|
| GET | `/recommendations/` | Filters: `status`, `severity`, `category`, `product`, `rule_code`. `search`. Default order: severity, then impact (both descending). |
| GET | `/recommendations/{id}/` | One recommendation |
| GET | `/recommendations/summary/` | Open counts by severity and category, plus total impact |
| POST | `/recommendations/{id}/complete/` | `open` → `done` |
| POST | `/recommendations/{id}/dismiss/` | `open` → `dismissed` |
| POST | `/recommendations/{id}/reopen/` | `done`/`dismissed` → `open` |

Invalid transitions return **409 Conflict**.

```json
// GET /api/recommendations/?status=open  (one item)
{
  "id": 7,
  "product": { "id": 9, "asin": "B0158CA34B", "title": "Digital Kitchen Scale 11lb" },
  "rule_code": "low_stock", "category": "inventory",
  "severity": 3, "severity_label": "High",
  "title": "Restock Digital Kitchen Scale 11lb",
  "message": "Only 5 days of stock left at 52.4 units/day. Replenishment takes about 21 days, so reorder ~2,428 units now to avoid a stockout.",
  "estimated_impact": "15381.45",
  "evidence": { "inventory_qty": 246, "avg_daily_units": 52.43, "days_of_cover": 4.7, "reorder_qty": 2428 },
  "status": "open",
  "created_at": "2026-11-16T20:13:41Z", "updated_at": "2026-11-16T20:14:32Z", "resolved_at": null
}
```

## Sync

| Method | Path | Description |
|---|---|---|
| POST | `/sync/` | Run a marketplace sync now. `201` with the SyncJob on success, `502` with the SyncJob (including `error`) if the marketplace failed, `409` if a sync is already running, `429` if throttled (20/hour by default). |
| GET | `/sync/jobs/` | Sync history, newest first |
| GET | `/sync/jobs/{id}/` | One sync job |

```json
// POST /api/sync/
{
  "id": 2, "source": "mock", "status": "success",
  "started_at": "2026-11-16T20:14:32.239Z", "finished_at": "2026-11-16T20:14:32.455Z",
  "duration_ms": 215, "triggered_by": "demo",
  "products_upserted": 12, "metrics_upserted": 720,
  "recommendations_created": 0, "recommendations_updated": 8, "recommendations_expired": 0,
  "error": ""
}
```

## Errors

| Status | Meaning |
|---|---|
| 400 | Validation error. The body maps field names to messages. |
| 401 | Missing or expired token |
| 403 | Authenticated but not attached to a brand |
| 404 | Not found, **or belongs to another brand** (existence is not revealed) |
| 409 | Invalid state transition, or a sync is already running |
| 429 | Throttled |
| 502 | The marketplace API failed during a sync |

## Health

`GET /api/health/` returns `{"status": "ok"}` without authentication, for load balancers and
container health checks.
