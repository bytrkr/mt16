from __future__ import annotations
import time, random
from typing import Any, Dict, Optional, Tuple

import requests

DEFAULT_HEADERS = {
    "User-Agent": "MT16-OSINT/1.9 (+localhost; safe-collector)",
    "Accept": "*/*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.7,en;q=0.6",
    "Connection": "close",
}

BLOCK_KEYWORDS = [
    "captcha",
    "cloudflare",
    "attention required",
    "verify you are human",
    "robot",
    "access denied",
    "login required",
    "sign in",
]

def looks_blocked(status: int, text: str) -> bool:
    if status in (401, 403, 429):
        return True
    low = (text or "").lower()
    return any(k in low for k in BLOCK_KEYWORDS)

def backoff_sleep(attempt: int) -> None:
    # exponential backoff with jitter (vakar ve sabır)
    base = min(60.0, (2 ** min(attempt, 6)))
    jitter = random.uniform(0.25, 1.25)
    time.sleep(base * jitter)

def safe_get(url: str, timeout: int = 25, max_attempts: int = 4) -> Tuple[bool, Dict[str, Any]]:
    last_err = None
    for attempt in range(max_attempts):
        try:
            r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            text = r.text or ""
            blocked = looks_blocked(r.status_code, text)
            meta = {
                "ok": (200 <= r.status_code < 300) and (not blocked),
                "status": r.status_code,
                "blocked": blocked,
                "url": url,
                "bytes": len(r.content or b""),
                "content_type": r.headers.get("content-type", ""),
                "text_sample": text[:800],
            }
            if meta["ok"]:
                meta["text"] = text
            return meta["ok"], meta
        except Exception as e:
            last_err = str(e)
            backoff_sleep(attempt)
    return False, {"ok": False, "url": url, "error": last_err or "unknown"}
