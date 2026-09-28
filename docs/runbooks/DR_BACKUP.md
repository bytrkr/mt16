# MT16 Felaket Kurtarma (DR) & Backup

Kritik varlıklar:
- replay/events.log
- OPA policy bundle
- Helm values
- image digest kayıtları

RPO: 24h
RTO: 60m

DR Senaryosu (cluster kaybı):
1) yeni cluster + Istio
2) Helm install
3) replay log restore
4) doğrulama
