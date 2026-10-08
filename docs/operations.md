# Operations guide

```sh
kubectl -n data-observability get events --sort-by=.lastTimestamp
kubectl -n data-observability logs job/init-db
kubectl -n data-observability logs deployment/api
kubectl -n data-observability logs deployment/prometheus
kubectl -n data-observability logs deployment/grafana
```

- Pending PostgreSQL: verify Minikube's default StorageClass and available disk. Its PVC survives ordinary pod replacement.
- ImagePullBackOff on API: build the image inside the active Minikube profile with the exact `data-observability-api:local` tag.
- Failed init Job: inspect credentials and PostgreSQL readiness. After fixing the cause, delete only `job/init-db` and reapply `k8s/init-db.yaml`.
- Empty charts: check both Prometheus targets, generate traffic, and wait at least 30 seconds. Port forwarding can stop if its selected pod is replaced; restart it.
- Updated API: rebuild the image, then run `kubectl -n data-observability rollout restart deployment/api`.
- Updated monitoring configuration: apply Kustomize again. ConfigMap hashes update pod templates, triggering replacement.
- Changing PostgreSQL Secret values does not change passwords inside an existing database volume. Change the database role password explicitly and update its connection string together.

To remove the entire demo, run `kubectl delete namespace data-observability`. **This deletes the namespace and its PVCs and can destroy demo data.** Use `minikube stop` to pause the cluster without deliberately deleting resources.

## Scope and limitations

This is a portfolio demonstrator, not a production or Acceldata product. It validates one event schema and measures freshness, validity, duplicates, availability, and latency. It does not implement data lineage, statistical drift detection, arbitrary dataset profiling, or distributed tracing.

PostgreSQL has one replica and no backups or failover. Prometheus and Grafana use ephemeral volumes; their history and UI edits are lost on replacement, while provisioned dashboards reload from source. There is no TLS ingress, tenant isolation, NetworkPolicy, rate limiting, request-size cap, or database retention policy. Use an authenticated gateway and resource controls before any public exposure. Dependencies and images have fixed baseline versions, not a claim of being the latest or vulnerability-free; review updates and scan images before deployment. Dependabot covers Python, Dockerfile, and Actions updates; review Kubernetes image tags separately.
