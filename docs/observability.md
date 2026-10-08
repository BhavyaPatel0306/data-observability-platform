# Metrics and alerts

`dop_events_total{outcome}` records accepted, rejected, duplicate, and db_error outcomes. Rejected counts schema failures; authentication failures are excluded. `dop_stale_events_total` counts accepted stale events. `dop_ingest_duration_seconds` measures all POST ingestion requests including failures. `dop_event_age_seconds` measures accepted event age. No user IDs or source strings are metric labels, preventing unbounded time-series cardinality.

Prometheus alerts cover rejection ratios above 10%, stale ratios above 10%, database write errors, and no available API scrape targets. The Grafana dashboard displays firing Prometheus alerts, while **Alerting → Alert rules** includes a separate Grafana-managed database-error rule. These are live alert states; external email/Slack delivery is not configured. Add a contact point and notification policy for Grafana delivery, or an Alertmanager for Prometheus notifications.

Metrics live in each API process and reset on restart. Run one Uvicorn worker per pod. Prometheus discovers pod IPs instead of scraping a load-balanced Service, so both replicas contribute correctly. Metrics are operational observations, not an exactly-once accounting ledger: a process crash between commit and counter increment can undercount accepted events.

## References

- [Prometheus configuration and Kubernetes discovery](https://prometheus.io/docs/prometheus/latest/configuration/)
- [Grafana dashboard and datasource provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Grafana file-based alert provisioning](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/file-provisioning/)
