# Run locally with Minikube

Install Docker Desktop (Linux containers), Minikube, kubectl, and Python 3.12. Start Docker first. Allocate roughly 4 CPUs and 6 GiB RAM. Run commands from this repository's root. The Kubernetes commands work in PowerShell and Bash.

```sh
minikube start --cpus=4 --memory=6144
minikube image build -t data-observability-api:local .
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.example.yaml
kubectl apply -k .
kubectl -n data-observability wait --for=condition=complete job/init-db --timeout=240s
kubectl -n data-observability rollout status deployment/api --timeout=240s
kubectl -n data-observability rollout status deployment/prometheus --timeout=240s
kubectl -n data-observability rollout status deployment/grafana --timeout=240s
kubectl -n data-observability get pods,pvc
```

The example credentials are deliberately public, local-demo-only values. Applying the example Secret is an explicit step; Kustomize does not include it. To customize, copy it to the ignored `k8s/secret.local.yaml`, edit all credentials, and apply that file instead. Update `DATABASE_URL` consistently with the PostgreSQL fields; URL-encode special characters in its password. Kubernetes Secrets are not inherently encrypted credentials. Do not expose this demo publicly with example credentials.

Open three separate terminals and leave these commands running:

```sh
kubectl -n data-observability port-forward service/api 8000:8000
kubectl -n data-observability port-forward service/prometheus 9090:9090
kubectl -n data-observability port-forward service/grafana 3000:3000
```

Visit:

- API docs: <http://localhost:8000/docs>. Enter the key in each endpoint's `x-api-key` header field.
- Prometheus: <http://localhost:9090/targets> and <http://localhost:9090/alerts>.
- Grafana: <http://localhost:3000>, user `admin`, password `local-demo-grafana-change-me`.
- Grafana dashboard: <http://localhost:3000/d/data-observability>.

Generate traffic in a fourth terminal. PowerShell:

```powershell
$env:INGEST_API_KEY = 'local-demo-api-key-change-me'
python scripts/generate_data.py --count 1800 --interval 0.2
```

Bash:

```sh
export INGEST_API_KEY=local-demo-api-key-change-me
python scripts/generate_data.py --count 1800 --interval 0.2
```

This produces about six minutes of traffic: roughly 15% invalid submissions and 20% stale events. Rates need at least two scrapes; alert windows and pending periods take several minutes. HTTP 422 is expected for intentionally invalid events. The script reports response counts. To generate only clean data, use `--invalid-rate 0 --stale-rate 0`.

To verify monitoring after the ports are forwarded (PowerShell):

```powershell
$env:GRAFANA_USER = 'admin'
$env:GRAFANA_PASSWORD = 'local-demo-grafana-change-me'
python scripts/smoke_monitoring.py
```

For Bash set the same variables with `export`. The smoke check expects the default two replicas.
