from __future__ import annotations
from typing import Any, Dict, List, Optional

import os

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

from mt16.core.storage import now_iso, stable_hash_record, write_json, append_index, list_index
from mt16.ingestion.collectors import collect_rss, collect_public_page
from mt16.analysis.engine import analyze_record

APP_VERSION = "1.9"

def build_app(base_dir: str) -> FastAPI:
    app = FastAPI(title="MT16", version=APP_VERSION)

    mem_dir = os.path.join(base_dir, "mt16", "memory")
    ensure = lambda p: os.makedirs(p, exist_ok=True)
    ensure(mem_dir)

    index_path = os.path.join(mem_dir, "index.json")
    scores_path = os.path.join(mem_dir, "scores.json")

    def load_scores() -> Dict[str, Any]:
        if os.path.exists(scores_path):
            try:
                import json
                with open(scores_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"logic": [], "authority": []}
        return {"logic": [], "authority": []}

    def save_scores(s: Dict[str, Any]) -> None:
        write_json(scores_path, s)

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {"ok": True, "version": APP_VERSION, "time": now_iso()}

    @app.post("/collect")
    def collect(body: Dict[str, Any] = Body(...)) -> JSONResponse:
        """
        body:
          {
            "uid": "local",
            "targets": [
              {"kind":"rss","url":"https://.../feed.xml"},
              {"kind":"page","url":"https://..."}
            ]
          }
        """
        uid = str(body.get("uid") or "local")
        targets = body.get("targets") or []
        if not isinstance(targets, list) or not targets:
            return JSONResponse(status_code=400, content={"ok": False, "error": "targets required"})

        results = []
        manual = []
        for t in targets[:25]:
            if not isinstance(t, dict):
                continue
            kind = str(t.get("kind") or "").lower()
            url = str(t.get("url") or "").strip()
            if not url:
                continue

            if kind == "rss":
                ok, payload = collect_rss(url)
            else:
                ok, payload = collect_public_page(url)

            if not ok:
                # engel / hata -> manuel müdahale raporu
                manual.append({
                    "time": now_iso(),
                    "url": url,
                    "kind": kind,
                    "reason": payload.get("error") or ("blocked" if payload.get("blocked") else "fetch_failed"),
                    "status": payload.get("status"),
                    "note": "MANUEL_MUDAHALE: Engel tespit edildi. Bypass YOK. Hedefi değiştir veya resmi API/RSS kullan.",
                })
                continue

            record = {
                "time": now_iso(),
                "uid": uid,
                "kind": kind,
                "payload": payload,
            }
            rid = stable_hash_record(record)
            record["rid"] = rid

            # persist
            rec_path = os.path.join(mem_dir, f"{rid}.json")
            write_json(rec_path, record)
            append_index(index_path, {"rid": rid, "time": record["time"], "kind": kind, "url": url})

            results.append({"rid": rid, "url": url, "kind": kind})

        out = {"ok": True, "collected": results, "manual_intervention": manual, "time": now_iso()}
        return JSONResponse(status_code=200, content=out)

    @app.post("/analyze")
    def analyze(body: Dict[str, Any] = Body(...)) -> JSONResponse:
        """
        body:
          {"rids": ["..."]}  veya {"latest": 10}
        """
        scores = load_scores()
        hist_logic = list(scores.get("logic") or [])[-250:]
        hist_auth = list(scores.get("authority") or [])[-250:]

        rids = body.get("rids")
        latest = body.get("latest")

        selected: List[str] = []
        if isinstance(rids, list) and rids:
            selected = [str(x) for x in rids[:25]]
        else:
            try:
                n = int(latest) if latest is not None else 10
            except Exception:
                n = 10
            idx = list_index(index_path)
            selected = [str(it.get("rid")) for it in idx[-max(1, min(50, n)):] if isinstance(it, dict) and it.get("rid")]

        analyzed = []
        for rid in selected:
            path = os.path.join(mem_dir, f"{rid}.json")
            if not os.path.exists(path):
                continue
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    record = json.load(f)
            except Exception:
                continue

            res = analyze_record(record, hist_logic, hist_auth)
            analyzed.append({"rid": rid, "time": record.get("time"), "result": res})

            # update history
            hist_logic.append(float(res["logic"]))
            hist_auth.append(float(res["authority"]))

        scores["logic"] = hist_logic[-500:]
        scores["authority"] = hist_auth[-500:]
        save_scores(scores)

        return JSONResponse(status_code=200, content={"ok": True, "count": len(analyzed), "items": analyzed, "time": now_iso()})

    @app.post("/report")
    def report(body: Dict[str, Any] = Body(...)) -> JSONResponse:
        """
        body:
          {"latest": 15}
        """
        try:
            n = int(body.get("latest") or 15)
        except Exception:
            n = 15
        n = max(1, min(50, n))

        idx = list_index(index_path)
        last = idx[-n:]

        # basit hüküm: son analiz sonuçları yoksa analyze çağrısı önerilir
        summary = {
            "hukum": "IZLEME",
            "emir": [
                "Önce /analyze çağrısı yap; anomali ve skorlar güncellensin.",
                "Engel tespit edilen hedefler için resmi RSS/API tercih et.",
            ],
            "cui_bono": "Cui Bono? (Kimin yararına?) sorusu her raporda korunur.",
        }

        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "version": APP_VERSION,
                "time": now_iso(),
                "index_tail": last,
                "summary": summary,
            },
        )

    return app
