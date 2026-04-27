---
title: Platform Release Notes
stripe: true
---

# Platform Release Notes

Release history for the Acme Platform API. Entries are listed newest first.

---

## v2.2.0 - April 18, 2026

### New Features

- **Streaming responses** on `/v1/export` endpoints - large datasets are now streamed rather than buffered, reducing memory usage and time-to-first-byte
- **Batch mutations** - up to 100 write operations can now be submitted in a single request via `POST /v1/batch`
- **Webhook retry configuration** - retry count and backoff multiplier are now configurable per webhook endpoint

### Improvements

- Reduced p99 latency on `/v1/query` by 34% following index optimisation on the `events` table
- SDK error messages now include a `request_id` field to simplify support escalation
- Dashboard now shows live rate limit consumption per API key

### Bug Fixes

- Fixed incorrect `Content-Length` header on CSV export responses
- Fixed edge case where `401` was returned instead of `403` for requests using a valid but insufficiently scoped key
- Fixed SDK retry logic that could produce duplicate requests under high network jitter

:::danger
`POST /v1/batch` replaces the deprecated `POST /v1/bulk` endpoint, which has been removed in this release. Update any clients still using `/v1/bulk` before upgrading.
:::

---

## v2.1.3 - March 31, 2026

### Bug Fixes

- Fixed pagination cursor corruption when result sets contained null `updated_at` values
- Fixed webhook signature verification failure when payload exceeded 64 KB
- Fixed memory leak in the connection pool under sustained high concurrency

:::warning
If you are running v2.1.0–v2.1.2 and processing webhook payloads larger than 64 KB, upgrade immediately - signature verification silently passes invalid signatures on affected versions.
:::

---

## v2.1.0 - March 3, 2026

### New Features

- **CSV export** on all collection endpoints via `Accept: text/csv`
- **Public API keys** - read-only keys safe for use in browser clients
- **Audit log API** - programmatic access to account activity at `/v1/audit`

### Breaking Changes

:::danger
The `data.results` field is renamed to `data.items` across all list responses. Clients on v2.0.x must update field references before migrating to v2.1.x.
:::

---

## v2.0.0 - January 14, 2026

Initial v2 release. See the [v2 migration guide](#) for full details.

### Highlights

- New scoped API key system (Public, Secret, Admin)
- Unified error response format across all endpoints
- Rate limit headers on every response (`X-RateLimit-*`)

### Removed

- XML response format (deprecated in v1.8)
- `/v1/legacy/*` endpoint namespace
- `api_key` query parameter authentication (use `Authorization` header)
