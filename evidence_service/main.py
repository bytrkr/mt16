import os
import re
import math
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
import yaml
from fastapi import FastAPI, HTTPException


app = FastAPI(title="MT16 Evidence Service (V26)")


DEFAULT_REGISTRY_PATH = os.getenv("SOURCES_REGISTRY_PATH", "evidence_service/config/sources.yaml")
GDELT_DOC_API = os.getenv("GDELT_DOC_API", "https://api.gdeltproject.org/api/v2/doc/doc")
FETCH_TIMEOUT_SEC = float(os.getenv("EVIDENCE_FETCH_TIMEOUT_SEC", "8"))
MAX_ARTICLES = int(os.getenv("EVIDENCE_MAX_ARTICLES", "10"))
RECENCY_HALF_LIFE_DAYS = float(os.getenv("EVIDENCE_RECENCY_HALF_LIFE_DAYS", "30"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _load_registry(path: str) -> Dict[str, Dict[str, Any]]:
    # Support container-relative and project-relative paths.
    candidates = [path, os.path.join("/app", path), os.path.join(os.getcwd(), path)]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            return doc.get("verified_sources", {}) or {}
    return {}


REGISTRY = _load_registry(DEFAULT_REGISTRY_PATH)


def _domain_of(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.lower()
    except Exception:
        return ""


def _match_registry(domain: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Suffix-match the allowlist: if the registry contains `reuters.com`,
    then `www.reuters.com` matches it.
    """
    if not domain:
        return None
    for key, meta in REGISTRY.items():
        k = key.lower().strip()
        if domain == k or domain.endswith("." + k):
            return k, meta
    return None


def _extract_published_time(html: str) -> Optional[datetime]:
    """
    Best-effort extraction from common meta tags.
    """
    patterns = [
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']pubdate["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']og:updated_time["\'][^>]+content=["\']([^"\']+)["\']',
        r'"datePublished"\s*:\s*"([^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, html, flags=re.IGNORECASE)
        if not m:
            continue
        raw = m.group(1).strip()
        for fmt in (
            None,  # use fromisoformat parser below
        ):
            try:
                # Normalize Z
                s = raw.replace("Z", "+00:00")
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue
    return None


def _recency_weight(published_at: Optional[datetime]) -> float:
    if not published_at:
        return 0.50  # unknown recency: conservative neutral
    age_sec = max(0.0, (_utc_now() - published_at).total_seconds())
    age_days = age_sec / 86400.0
    # Exponential decay with half-life.
    return float(2 ** (-age_days / max(1e-6, RECENCY_HALF_LIFE_DAYS)))


_WORD_RE = re.compile(r"[a-zA-Z0-9]+", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "") if len(t) >= 3]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _agreement_score(texts: List[str]) -> float:
    tokens = [_tokenize(t) for t in texts if t]
    if len(tokens) < 2:
        return 0.0
    scores = []
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens)):
            scores.append(_jaccard(tokens[i], tokens[j]))
    return float(sum(scores) / max(1, len(scores)))


def _detect_flags(text: str) -> List[str]:
    t = (text or "").lower()
    flags = []
    speculative = ["could", "may", "might", "reportedly", "rumor", "unconfirmed", "sources said"]
    advert = ["sponsored", "advertisement", "promo", "promotion", "affiliate", "partnered"]
    manip = ["shocking", "you won't believe", "miracle", "guaranteed", "secret revealed", "click here"]

    if any(k in t for k in speculative):
        flags.append("SPECULATIVE_RISK")
    if any(k in t for k in advert):
        flags.append("ADVERTISEMENT_RISK")
    if any(k in t for k in manip):
        flags.append("MANIPULATION_RISK")
    return flags


async def _gdelt_search(query: str) -> List[str]:
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(MAX_ARTICLES),
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_SEC) as client:
        r = await client.get(GDELT_DOC_API, params=params)
        r.raise_for_status()
        data = r.json()
    articles = data.get("articles") or []
    urls = []
    for a in articles:
        u = a.get("url")
        if u:
            urls.append(u)
    return urls


async def _fetch_article(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_SEC, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "MT16-Evidence/1.0"})
        r.raise_for_status()
        html = r.text

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", (title_m.group(1) if title_m else "")).strip()
    desc_m = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )
    description = (desc_m.group(1).strip() if desc_m else "")
    published_at = _extract_published_time(html)

    text_for_flags = " ".join([title, description])
    return {
        "url": url,
        "title": title[:300],
        "snippet": description[:500],
        "published_at": published_at.isoformat() if published_at else None,
        "flags": _detect_flags(text_for_flags),
    }


def _label(score: float, sources_count: int) -> str:
    if sources_count >= 2 and score >= 0.80:
        return "VERIFIED"
    if sources_count >= 1 and score >= 0.55:
        return "PARTIALLY_VERIFIED"
    return "UNVERIFIED"


def _compute_verification(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not sources:
        return {
            "sources_count": 0,
            "recency_score": 0.0,
            "agreement_score": 0.0,
            "verification_score": 0.0,
            "label": "UNVERIFIED",
            "flags": ["NO_VERIFIED_SOURCES_FOUND"],
        }

    recencies = []
    trust_rec = []
    texts = []
    all_flags = []

    for s in sources:
        # Recency
        published_raw = s.get("published_at")
        published_dt = None
        if published_raw:
            try:
                published_dt = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
                published_dt = published_dt.astimezone(timezone.utc)
            except Exception:
                published_dt = None
        r_w = _recency_weight(published_dt)
        recencies.append(r_w)

        # Trust×recency
        trust = float(s.get("trust", 0.0))
        trust_rec.append(trust * r_w)

        # Agreement text
        texts.append((s.get("title") or "") + " " + (s.get("snippet") or ""))

        # Flags
        all_flags.extend(s.get("flags") or [])

    agreement = _agreement_score(texts)
    recency_score = float(sum(recencies) / max(1, len(recencies)))
    base = float(sum(trust_rec) / max(1, len(trust_rec)))
    verification = base * (0.50 + 0.50 * agreement)
    verification = max(0.0, min(1.0, verification))

    agg_flags = sorted(set(all_flags))
    if agreement < 0.25 and len(texts) >= 2:
        agg_flags.append("LOW_AGREEMENT")
    return {
        "sources_count": len(sources),
        "recency_score": recency_score,
        "agreement_score": agreement,
        "verification_score": verification,
        "label": _label(verification, len(sources)),
        "flags": sorted(set(agg_flags)),
    }


@app.post("/collect")
async def collect(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      - { "query": "<string>" } OR
      - { "claims": [{"text":"...", "type":"economy|health|general"}] }
    Output:
      - If query: { ...claim_evidence... }
      - If claims: { "claims": [ ...per-claim evidence... ] }
    """
    if "claims" in payload and isinstance(payload["claims"], list):
        out = []
        for c in payload["claims"]:
            text = (c or {}).get("text", "")
            ctype = (c or {}).get("type", "general")
            out.append(await _collect_one(text, ctype))
        return {"claims": out}

    query = str(payload.get("query", "")).strip()
    ctype = str(payload.get("type", "general")).strip() or "general"
    return await _collect_one(query, ctype)


async def _collect_one(claim_text: str, claim_type: str) -> Dict[str, Any]:
    claim_text = (claim_text or "").strip()
    if not claim_text:
        raise HTTPException(status_code=400, detail="Missing claim text")

    urls: List[str] = []
    try:
        urls = await _gdelt_search(claim_text)
    except Exception:
        # Offline / blocked environment: fail closed, return no evidence.
        urls = []

    verified_sources: List[Dict[str, Any]] = []
    for u in urls:
        domain = _domain_of(u)
        match = _match_registry(domain)
        if not match:
            continue
        reg_domain, meta = match
        try:
            article = await _fetch_article(u)
        except Exception:
            continue

        article["domain"] = reg_domain
        article["trust"] = float(meta.get("trust", 0.0))
        article["category"] = str(meta.get("category", "unknown"))
        verified_sources.append(article)

    metrics = _compute_verification(verified_sources)
    return {
        "claim": claim_text,
        "claim_type": claim_type,
        "sources": verified_sources,
        **metrics,
    }
