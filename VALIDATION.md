# Delivery validation

Validated on October 7, 2026, with Python 3.12 on Windows.

- `pytest -q`: **15 passed** using temporary SQLite databases. Covers ingestion and retrieval, durable row insertion, duplicate conflicts, eight invalid-payload cases, authentication, stale-data metrics, health endpoints, database failure responses, missing events, YAML/JSON parsing, Kustomize input paths, and explicit example-secret opt-in.
- `ruff check app tests scripts`: **passed**.
- One dependency deprecation warning: Starlette's test client references AnyIO's deprecated `BlockingPortal` alias. It does not fail the tests.

The first test attempt could not create its sandbox temporary directories. Running with an approved local temporary directory resolved this environment issue.

## GitHub Actions: passed

[CI run 37722066394](https://github.com/BhavyaPatel0306/data-observability-platform/actions/runs/37722066394) passed for implementation commit `430a8d8` on October 7, 2026 (America/Toronto).

- Python lint and the full 15-test suite passed on Ubuntu.
- All 13 API tests passed against a real PostgreSQL 16 service.
- Prometheus configuration syntax and alert-rule evaluation tests passed.
- The API Docker image built successfully.
- A Kind Kubernetes cluster accepted the manifests, completed schema initialization, and rolled out the API, Prometheus, and Grafana.
- Sample event traffic completed successfully.
- The monitoring smoke check verified both API scrape targets were healthy, all four Prometheus rules were loaded, the six-panel Grafana dashboard was provisioned, and the Grafana-managed database-error rule existed.

Not directly verified: Minikube on this Windows machine, visual dashboard rendering in a browser, end-to-end Grafana alert firing, external notification delivery, volume recovery, or production performance. Docker, kubectl, and Minikube were unavailable locally; the cluster checks above ran on GitHub's Ubuntu runner using Kind. No throughput or uptime claims were measured.
