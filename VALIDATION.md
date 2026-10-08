# Delivery validation

Validated on October 7, 2026, with Python 3.12 on Windows.

- `pytest -q`: **15 passed** using temporary SQLite databases. Covers ingestion and retrieval, durable row insertion, duplicate conflicts, eight invalid-payload cases, authentication, stale-data metrics, health endpoints, database failure responses, missing events, YAML/JSON parsing, Kustomize input paths, and explicit example-secret opt-in.
- `ruff check app tests scripts`: **passed**.
- One dependency deprecation warning: Starlette's test client references AnyIO's deprecated `BlockingPortal` alias. It does not fail the tests.

The first test attempt could not create its sandbox temporary directories. Running with an approved local temporary directory resolved this environment issue.

Not executed here: PostgreSQL integration, Docker image build, Minikube/Kind deployment, Kubernetes server validation, Prometheus `promtool` checks, dashboard rendering, Grafana alert evaluation, or hosted GitHub Actions. Docker, kubectl, and Minikube were unavailable in the execution environment. SQLite tests do not establish PostgreSQL or cluster compatibility.

The included CI workflow performs the PostgreSQL tests, Prometheus rule checks, and Kind deployment/smoke checks when pushed to GitHub. Those checks are **configured, not yet observed passing**. The Minikube guide provides the equivalent local deployment path. No throughput, uptime, or production-performance claims were measured.
