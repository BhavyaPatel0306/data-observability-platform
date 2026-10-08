"""Verify real Prometheus targets and provisioned Grafana artifacts after port-forwarding."""
import base64
import json
import os
from urllib.request import Request, urlopen


def get(url, auth=None):
    headers = {"Authorization": "Basic " + base64.b64encode(auth.encode()).decode()} if auth else {}
    with urlopen(Request(url, headers=headers), timeout=10) as response:
        return json.load(response)


targets = get("http://localhost:9090/api/v1/targets")["data"]["activeTargets"]
api_targets = [t for t in targets if t["labels"].get("job") == "ingest-api"]
assert len(api_targets) == 2, api_targets
assert all(t["health"] == "up" for t in api_targets), api_targets
rules = get("http://localhost:9090/api/v1/rules")["data"]["groups"]
assert any(g["name"] == "data-quality" and len(g["rules"]) == 4 for g in rules), rules
auth = os.environ["GRAFANA_USER"] + ":" + os.environ["GRAFANA_PASSWORD"]
dashboard = get("http://localhost:3000/api/dashboards/uid/data-observability", auth)
assert len(dashboard["dashboard"]["panels"]) == 6
alert = get("http://localhost:3000/api/v1/provisioning/alert-rules/ingestion-database-errors", auth)
assert alert["title"] == "Ingestion database errors"
print("Both API scrape targets, four Prometheus rules, dashboard, and Grafana alert verified.")
