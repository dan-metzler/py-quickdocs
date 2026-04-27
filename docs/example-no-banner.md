---
columns: true
columns: 3
---

# HTTP Status Code Reference

A reference guide to HTTP status codes returned by the API, with causes and recommended client behaviour for each.

![Remote image test - fetched at generation time](https://picsum.photos/seed/pymarkdown/900/300)

---

## 2xx - Success

### 200 OK

The request succeeded. The response body contains the requested resource or result.

```json
{
  "data": { "id": "abc123", "status": "active" },
  "meta": { "request_id": "req_9xKp2m" }
}
```

### 201 Created

A new resource was created. The `Location` header contains the URI of the new resource.

> Always check the `Location` header after a `201` rather than constructing the URI manually - resource ID formats may change between API versions.

### 204 No Content

The request succeeded and there is no response body. Common on `DELETE` requests.

---

## 4xx - Client Errors

These errors indicate a problem with the request. Fix the request before retrying - retrying immediately without changes will produce the same error.

### 400 Bad Request

The request body is malformed, missing required fields, or contains invalid values.

**Common causes:**

- Invalid JSON syntax
- Missing required field (`"field is required"`)
- Value outside allowed range (`"must be between 1 and 100"`)
- Wrong type (`"expected string, got integer"`)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required field: email",
    "field": "email"
  }
}
```

### 401 Unauthorized

No valid credentials were provided, or the credentials have expired.

- Check that the `Authorization: Bearer <token>` header is present and correctly formatted
- Verify the API key has not been revoked in the dashboard
- Token-based sessions expire after 24 hours - re-authenticate and use the new token

### 403 Forbidden

Valid credentials were provided but they do not have permission to perform this action.

| Key Type | Read | Write | Delete | Admin |
|----------|------|-------|--------|-------|
| Public   | ✓    | ✗     | ✗      | ✗     |
| Secret   | ✓    | ✓     | ✓      | ✗     |
| Admin    | ✓    | ✓     | ✓      | ✓     |

:::note
`403` is distinct from `401`. A `401` means *who are you?* A `403` means *I know who you are, but you can't do this.*
:::

### 404 Not Found

The requested resource does not exist, or the authenticated user does not have visibility of it.

:::tip!
Some endpoints return `404` instead of `403` for resources the caller lacks permission to see - this is intentional to avoid leaking the existence of private resources.
:::

### 409 Conflict

The request conflicts with the current state of the resource. Common on create operations when a unique constraint would be violated.

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "A webhook endpoint with this URL already exists",
    "existing_id": "wh_7mNpQr"
  }
}
```

### 422 Unprocessable Entity

The request is well-formed and the fields are valid types, but the combination of values is semantically invalid.

**Example:** creating a scheduled job with `start_at` in the past, or setting `max_retries` higher than the plan limit.

### 429 Too Many Requests

The rate limit for the API key has been exceeded.

**Response headers:**

| Header | Value |
|---|---|
| `X-RateLimit-Limit` | Maximum requests allowed in the window |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |
| `Retry-After` | Seconds to wait before retrying |

**Recommended backoff strategy:**

```python
import time

def with_backoff(fn, max_retries=5):
    for attempt in range(max_retries):
        result = fn()
        if result.status_code != 429:
            return result
        reset = int(result.headers.get("Retry-After", 2 ** attempt))
        time.sleep(reset)
    raise Exception("Rate limit not cleared after retries")
```

:::warning
Do not retry on `429` without honouring the `Retry-After` header. Ignoring it and retrying immediately will extend your penalty window on some plans.
:::

---

## 5xx - Server Errors

These errors originate from the server. The request may be safe to retry after a short delay.

### 500 Internal Server Error

An unexpected error occurred on the server. The response body includes a `request_id` - include this when contacting support.

### 502 Bad Gateway

The API gateway received an invalid response from an upstream service. Usually transient - retry with exponential backoff.

### 503 Service Unavailable

The service is temporarily unavailable, typically due to a planned maintenance window or overload shedding. Check the status page and retry after the `Retry-After` header value if present.

### 504 Gateway Timeout

The upstream service did not respond within the gateway timeout (30 seconds). Long-running operations should use the async job endpoints rather than synchronous requests.

:::danger
Never retry a mutating request (`POST`, `PUT`, `PATCH`, `DELETE`) on a `504` without first checking whether the operation was applied - the request may have completed on the server before the timeout. Use the `GET` endpoint to verify state before retrying.
:::

---

## Idempotency

For `POST` requests that create or mutate resources, pass an `Idempotency-Key` header to safely retry without risk of duplicate operations.

```http
POST /v1/payments
Authorization: Bearer YOUR_API_KEY
Idempotency-Key: a84f2c1e-9b3d-4f7a-8c2e-1d5f6a9b3e7c
Content-Type: application/json
```

- Keys must be unique per logical operation - use a UUID
- The server stores the result for 24 hours
- Repeating a request with the same key returns the original response without re-executing the operation
