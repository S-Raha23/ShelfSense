# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-11-17

### Added
- Brand-based multi-tenant accounts with JWT authentication (register, login, silent refresh).
- Catalog and `DailyMetric` fact table, plus a dashboard API (summary with period comparison,
  daily/weekly time series, top products).
- Marketplace integration layer: `MarketplaceClient` interface, deterministic mock Amazon adapter,
  documented SP-API adapter, and retries with exponential backoff and jitter.
- Sync service with re-run-safe upserts, a single transaction, per-brand locking, stale-job
  recovery, throttling and a `SyncJob` audit log.
- Recommendation engine with five rules (low stock, overstock, price gap, rating drop, low
  conversion), severity and impact estimates, a done/dismiss/reopen workflow, 14-day snooze and
  auto-expiry.
- React frontend: dashboard, products, product detail, recommendations and sync history pages.
  Optimistic updates, URL-synced date range, route-level code splitting, responsive layout.
- OpenAPI schema and Swagger UI at `/api/docs/`.
- Docker Compose deployment (PostgreSQL, gunicorn, nginx) and GitHub Actions CI.
- Documentation: architecture, recommendation engine, API reference, deployment guide.
