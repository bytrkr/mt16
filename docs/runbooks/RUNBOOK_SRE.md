# MT16 Operasyonel Runbook (SRE)

## Sistem Sağlık Kontrolü
- Core API: /docs (200)
- OPA: /v1/data/mt16/allow reachable
- Audit log: replay/events.log büyüyor
- Jaeger UI: trace görülebilir
- Prometheus: otel-collector target up

## Güncelleme
- Image build + push
- SBOM + scan + policy test
- Helm upgrade (digest pinned)
- Rollback: önceki digest ile geri dönüş
