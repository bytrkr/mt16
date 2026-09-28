from __future__ import annotations

import re
import json
import time
import hashlib
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import requests
import feedparser
from bs4 import BeautifulSoup

def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

BARRIER_PATTERNS = [
    r"captcha",
    r"cloudflare",
    r"access denied",
    r"verify you are human",
    r"login",
    r"sign in",
]

def detect_barrier(text: str) -> Optional[str]:
    t = (text or "").lower()
    for p in BARRIER_PATTERNS:
        if re.search(p, t):
            return p
    return None

def http_get(url: str, timeout: int = 25) -> Tuple[int, str, Dict[str, str]]:
    # Güvenli ve sade: agresif otomasyon yok.
    headers = {
        "User-Agent": "MT16-OSINT/1.8.1 (+localhost; senedli-muhakeme)",
        "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    text = r.text if hasattr(r, "text") else ""
    return r.status_code, text, dict(r.headers or {})

def collect_rss(url: str) -> Dict[str, Any]:
    # RSS parse: feedparser kendisi GET yapar; yine de kanıt metni saklanır.
    fp = feedparser.parse(url)
    items: List[Dict[str, Any]] = []
    for e in fp.entries[:30]:
        items.append({
            "title": getattr(e, "title", ""),
            "link": getattr(e, "link", ""),
            "published": getattr(e, "published", ""),
            "summary": getattr(e, "summary", ""),
        })
    raw = ""
    try:
        # kanıt: özet olarak feed meta + ilk entry başlıkları
        raw = json.dumps({"feed": fp.get("feed", {}), "titles": [i["title"] for i in items]}, ensure_ascii=False)[:20000]
    except Exception:
        raw = ""
    return {
        "kind": "rss",
        "url": url,
        "time": now_iso(),
        "items": items,
        "raw_excerpt": raw,
        "barrier": None,
    }

def collect_page(url: str) -> Dict[str, Any]:
    status, text, headers = http_get(url)
    barrier = detect_barrier(text)
    soup = BeautifulSoup(text, "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    # Sadece açık metin sinyali: ilk 4-6K karakter
    visible = soup.get_text(" ", strip=True)
    excerpt = (visible[:6000] if visible else "")
    return {
        "kind": "page",
        "url": url,
        "time": now_iso(),
        "status": status,
        "title": title,
        "headers": {k: headers.get(k, "") for k in ["content-type", "server"] if headers},
        "excerpt": excerpt,
        "barrier": barrier,
    }
