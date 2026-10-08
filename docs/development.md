# Development and testing

```sh
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` on PowerShell or `source .venv/bin/activate` on Bash, then:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check app tests scripts
```

Default API tests use isolated SQLite files for fast application-level verification. Set `TEST_DATABASE_URL` to a **disposable PostgreSQL database** to run the same tests against PostgreSQL. Tests delete events and exercise dropping/recreating the table; never point them at real data. CI creates its own PostgreSQL service.

To run the API without Kubernetes, start a local PostgreSQL instance, set `DATABASE_URL` to a SQLAlchemy `postgresql+psycopg://...` URL and `INGEST_API_KEY` to a string of at least 16 characters, then:

```sh
python -m app.init_db
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

For a lightweight development-only run, `DATABASE_URL=sqlite:///local.db` also works. PostgreSQL is the deployed backend. Schema creation is intentionally a separate operation to avoid races between replicas; future schema changes need migrations.

CI runs lint, SQLite and PostgreSQL API tests, Prometheus syntax/rule tests, builds the image, deploys to Kind, generates events, and checks both scrape targets and Grafana provisioning. A workflow file being present is not evidence that hosted CI has passed; check the Actions run after pushing.
