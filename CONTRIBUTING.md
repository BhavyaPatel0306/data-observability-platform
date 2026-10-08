# Contributing

Start with the [development guide](docs/development.md). Keep changes focused and include a reproducible explanation of the behavior being changed.

1. Create a branch for your change.
2. Update code and relevant documentation together.
3. Run `python -m pytest -q` and `ruff check app tests scripts`.
4. For database changes, run the tests against a disposable PostgreSQL database. The tests delete data.
5. For monitoring or Kubernetes changes, complete the Minikube walkthrough and monitoring smoke check.
6. Open a pull request and describe the validation you actually performed.

Never commit real credentials, local environments, or generated caches. Keep metrics labels bounded. Preserve one Uvicorn worker per API pod unless multiprocess metrics are explicitly implemented.
