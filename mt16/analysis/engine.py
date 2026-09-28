from __future__ import annotations
from typing import Any, Dict, List, Tuple

from mt16.analysis.scoring import authority_score, logic_score, anomaly_score

def summarize_items(payload: Dict[str, Any]) -> str:
    # build a compact string for scoring
    if payload.get("source") == "rss":
        titles = []
        for it in (payload.get("items") or [])[:10]:
            if isinstance(it, dict) and it.get("title"):
                titles.append(str(it["title"]))
        return " | ".join(titles)[:2500]
    if payload.get("source") == "page":
        t = payload.get("title") or ""
        s = payload.get("text_sample") or ""
        return (t + " " + s)[:2500]
    return str(payload)[:2500]

def analyze_record(record: Dict[str, Any], history_logic: List[float], history_auth: List[float]) -> Dict[str, Any]:
    payload = record.get("payload") or {}
    source = payload.get("source") or "unknown"
    url = payload.get("url") or payload.get("feed_url")
    text = summarize_items(payload)

    a = authority_score(str(source), str(url) if url else None)
    l = logic_score(text)

    a_anom = anomaly_score(history_auth, a)
    l_anom = anomaly_score(history_logic, l)

    # "Cui bono" placeholder: v1.9 sadece soruyu rapora koyar, otomatik hüküm vermez
    return {
        "authority": round(a, 4),
        "logic": round(l, 4),
        "anom_authority": round(a_anom, 4),
        "anom_logic": round(l_anom, 4),
        "cui_bono_question": "Cui Bono? (Kimin yararına?)",
        "verdict": verdict(a, l, a_anom, l_anom),
    }

def verdict(a: float, l: float, a_anom: float, l_anom: float) -> str:
    # vakur sınıflandırma
    if a < 0.45 and l < 0.45:
        return "FASIT_HABER_ADAYI"
    if l_anom > 0.65 or a_anom > 0.65:
        return "SUPHELI_IDDIA"
    if a >= 0.65 and l >= 0.55:
        return "SENEDLI_BILGI_ADAYI"
    return "IZLEME"
