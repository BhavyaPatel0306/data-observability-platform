"""Stdlib-only sample traffic generator. Never prints the API key."""
import argparse
import json
import os
import random
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--interval", type=float, default=0.2)
    parser.add_argument("--invalid-rate", type=float, default=0.15)
    parser.add_argument("--stale-rate", type=float, default=0.2)
    args = parser.parse_args()
    if args.count < 1 or args.interval < 0 or not all(0 <= x <= 1 for x in (args.invalid_rate, args.stale_rate)):
        parser.error("count must be positive, interval nonnegative, and rates between 0 and 1")
    key = os.environ["INGEST_API_KEY"]
    counts = {}
    for _ in range(args.count):
        timestamp = datetime.now(timezone.utc) - timedelta(seconds=600 if random.random() < args.stale_rate else 0)
        payload = {"event_id": str(uuid4()), "source": random.choice(["orders", "payments", "inventory"]),
                   "value": -1 if random.random() < args.invalid_rate else round(random.uniform(1, 100), 2),
                   "event_time": timestamp.isoformat()}
        request = Request(args.url.rstrip("/") + "/v1/events", data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json", "X-API-Key": key})
        try:
            with urlopen(request, timeout=10) as response:
                status = response.status
        except HTTPError as exc:
            status = exc.code
        except URLError as exc:
            raise SystemExit(f"API unreachable: {exc.reason}") from None
        counts[status] = counts.get(status, 0) + 1
        if status in (401, 403):
            raise SystemExit("Authentication failed; check INGEST_API_KEY")
        time.sleep(args.interval)
    print(json.dumps(counts, indent=2))
    if any(status not in (201, 422) for status in counts):
        raise SystemExit("Unexpected API responses; inspect the counts and API logs")


if __name__ == "__main__":
    main()
