from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

AUTHORITY_HINTS = {
    # kaba bir başlangıç: zamanla içtihatla güçlenecek
    "reuters": 0.85,
    "bloomberg": 0.85,
    "sec.gov": 0.9,
    "europa.eu": 0.85,
    "gov": 0.8,
    "investing.com": 0.55,
    "tradingview.com": 0.55,
    "reddit.com": 0.4,
    "twitter.com": 0.35,
    "x.com": 0.35,
}

SUSPICIOUS_WORDS = [
    "kesin", "garanti", "sızdı", "şok", "skandal", "mutlak", "asla",
    "inside", "leak", "confirmed", "breaking",
]

def authority_score(url: str) -> float:
    u = (url or "").lower()
    best = 0.3
    for k, v in AUTHORITY_HINTS.items():
        if k in u:
            best = max(best, v)
    return round(best, 2)

def logic_score(text: str) -> float:
    t = (text or "").lower()
    if not t.strip():
        return 0.2
    # Basit tutarlılık: aşırı sansasyon kelimeleri düşürür
    penalty = 0.0
    for w in SUSPICIOUS_WORDS:
        if w in t:
            penalty += 0.05
    # çok kısa metin de zayıf sayılır
    base = 0.65
    if len(t) < 200:
        base -= 0.2
    s = max(0.1, min(0.95, base - penalty))
    return round(s, 2)

def verdict(authority: float, logic: float, barrier: bool) -> str:
    if barrier:
        return "MANUEL_MUDAHALE"
    if authority >= 0.75 and logic >= 0.65:
        return "SENEDLI_HABER"
    if authority >= 0.55 and logic >= 0.55:
        return "SUPHELI_IDDIA"
    return "FASIT_HABER"
