# API reference

`POST /v1/events` requires `X-API-Key` and a JSON body:

```json
{
  "event_id": "9d7b2567-642b-443e-a899-1c576c1f33d0",
  "source": "orders",
  "value": 42.5,
  "event_time": "2026-10-07T18:00:00Z"
}
```

Use the generator for current timestamps. `event_id` must be a UUID, `source` must match `[a-z][a-z0-9_-]{0,31}`, and `value` must be finite and between 0 and 1,000,000. Extra fields are rejected. Timestamps must have a timezone and cannot exceed server time by more than 60 seconds. Numeric strings are coerced by Pydantic; this is schema validation, not strict JSON-type validation.

Responses: `201` committed successfully, `401` bad/missing key, `409` duplicate ID, `422` invalid data, `503` database error. Stale events (older than five minutes) are accepted, persisted, and counted separately. UUID uniqueness is enforced by the database across replicas. A repeat ID always returns 409 even if its body matches; this API does not replay prior success responses. A client retry after an ambiguous connection failure may therefore receive 409 for an already committed event.

`GET /v1/events/{event_id}` retrieves a stored event with authentication; an unknown ID returns 404. `/health/live` checks the process, `/health/ready` checks that the database and events table are accessible, and `/metrics` exposes Prometheus metrics. Health and metrics routes are unauthenticated for cluster monitoring.
