from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from mt16.ingestion.collectors import collect_rss, collect_page
from mt16.analysis.scoring import authority_score, logic_score, verdict
from mt16.memory.store import MemoryStore
from mt16.core.llm import LocalLLM

# ----------------------------
# Pydantic modelleri (önce!)
# ----------------------------
class Target(BaseModel):
    kind: str = Field(..., description="rss|page")
    url: str = Field(...)

class CollectRequest(BaseModel):
    uid: str = Field("local")
    targets: List[Target] = Field(default_factory=list)

class CollectItem(BaseModel):
    rid: str
    url: str
    kind: str
    time: str
    barrier: Optional[str] = None

class CollectResponse(BaseModel):
    ok: bool
    collected: List[CollectItem]

class AnalyzeRequest(BaseModel):
    latest: int = Field(20, ge=1, le=200)

class AnalyzeItem(BaseModel):
    rid: str
    time: str
    url: str
    kind: str
    authority: float
    logic: float
    verdict: str
    barrier: Optional[str] = None

class AnalyzeResponse(BaseModel):
    ok: bool
    count: int
    items: List[AnalyzeItem]

class ReportRequest(BaseModel):
    latest: int = Field(20, ge=1, le=200)

class ReportResponse(BaseModel):
    ok: bool
    time: str
    summary: str
    items: List[AnalyzeItem]

class ChatRequest(BaseModel):
    uid: str = "local"
    message: str
    latest: int = Field(20, ge=1, le=200)

class ChatResponse(BaseModel):
    ok: bool
    time: str
    answer: str
    evidence_rids: List[str]

# ----------------------------
# Uygulama
# ----------------------------
def build_app() -> FastAPI:
    app = FastAPI(title="MT16 v1.8.1 - Nizam-ı Hafiye", version="1.8.1")

    base_dir = os.path.dirname(os.path.dirname(__file__))  # .../mt16
    mem_root = os.path.join(base_dir, "memory")
    store = MemoryStore(mem_root)

    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama2")
    llm = LocalLLM(ollama_url, ollama_model, timeout=int(os.environ.get("OLLAMA_TIMEOUT", "120")))

    SYSTEM = (
        "MT16 v1.8.1 - Senedli Muhakeme Disiplini.\n"
        "- Delilsiz iddia kurma.\n"
        "- Kanıt (sened) yoksa 'Şüpheli İddia' diye işaretle.\n"
        "- Engel/CAPTCHA/Login görülürse: BYPASS YOK. Sadece rapor.\n"
        "- Kullanıcıya kısa, hüküm odaklı cevap ver.\n"
    )

    INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>MT16 v1.8.1 - Chat</title>
  <style>
    body{font-family:Arial, sans-serif; max-width:900px; margin:30px auto; padding:0 12px;}
    .box{border:1px solid #ddd; border-radius:10px; padding:12px; margin:10px 0;}
    textarea{width:100%; height:90px;}
    button{padding:10px 14px; cursor:pointer;}
    .muted{color:#666; font-size:12px;}
    pre{white-space:pre-wrap;}
  </style>
</head>
<body>
  <h2>MT16 v1.8.1 — Nizam-ı Hafiye (Localhost)</h2>
  <div class="box">
    <div class="muted">Sohbet: Senedli cevap. Kanıt yoksa şüpheli olarak işaretlenir.</div>
    <textarea id="msg" placeholder="Sorunu yaz..."></textarea>
    <div style="display:flex; gap:10px; margin-top:10px;">
      <button onclick="sendChat()">Gönder</button>
      <button onclick="collectSample()">Örnek Collect</button>
      <button onclick="analyze()">Analyze</button>
      <button onclick="report()">Report</button>
    </div>
  </div>

  <div class="box">
    <div class="muted">Çıktı</div>
    <pre id="out"></pre>
  </div>

<script>
async function sendChat(){
  const msg = document.getElementById('msg').value;
  const r = await fetch('/chat', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({uid:'local', message: msg, latest: 20})
  });
  const j = await r.json();
  document.getElementById('out').textContent = JSON.stringify(j, null, 2);
}
async function collectSample(){
  const r = await fetch('/collect', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({uid:'local', targets:[
      {kind:'rss', url:'https://www.investing.com/rss/news_25.rss'}
    ]})
  });
  const j = await r.json();
  document.getElementById('out').textContent = JSON.stringify(j, null, 2);
}
async function analyze(){
  const r = await fetch('/analyze', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({latest: 25})
  });
  const j = await r.json();
  document.getElementById('out').textContent = JSON.stringify(j, null, 2);
}
async function report(){
  const r = await fetch('/report', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({latest: 25})
  });
  const j = await r.json();
  document.getElementById('out').textContent = JSON.stringify(j, null, 2);
}
</script>
</body>
</html>
"""

    @app.get("/", response_class=HTMLResponse)
    def root():
        return HTMLResponse(INDEX_HTML)

    @app.get("/health")
    def health():
        return {"ok": True, "time": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")}

    @app.post("/collect", response_model=CollectResponse)
    def collect(req: CollectRequest):
        collected: List[CollectItem] = []
        for t in req.targets:
            if t.kind == "rss":
                rec = collect_rss(t.url)
            elif t.kind == "page":
                rec = collect_page(t.url)
            else:
                rec = {"kind": t.kind, "url": t.url, "time": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
                       "barrier": "UNSUPPORTED_KIND"}
            # Engel varsa rapor kaydı düş
            if rec.get("barrier"):
                store.put_case({
                    "time": rec.get("time"),
                    "type": "MANUEL_MUDAHALE_RAPORU",
                    "reason": f"Barrier detected: {rec.get('barrier')}",
                    "url": rec.get("url"),
                    "kind": rec.get("kind"),
                })
            rid = store.put(rec)
            collected.append(CollectItem(rid=rid, url=rec.get("url",""), kind=rec.get("kind",""), time=rec.get("time",""), barrier=rec.get("barrier")))
        return CollectResponse(ok=True, collected=collected)

    @app.post("/analyze", response_model=AnalyzeResponse)
    def analyze(req: AnalyzeRequest):
        rows = store.latest(req.latest)
        items: List[AnalyzeItem] = []
        for r in rows:
            url = r.get("url","")
            kind = r.get("kind","")
            barrier = r.get("barrier")
            text = r.get("excerpt") or r.get("raw_excerpt") or ""
            a = authority_score(url)
            l = logic_score(text)
            v = verdict(a, l, bool(barrier))
            # analizi kayda al
            r2 = dict(r)
            r2["analysis"] = {"authority": a, "logic": l, "verdict": v}
            store.put(r2)
            items.append(AnalyzeItem(
                rid=r.get("rid",""),
                time=r.get("time",""),
                url=url,
                kind=kind,
                authority=a,
                logic=l,
                verdict=v,
                barrier=barrier,
            ))
        return AnalyzeResponse(ok=True, count=len(items), items=items)

    @app.post("/report", response_model=ReportResponse)
    def report(req: ReportRequest):
        rows = store.latest(req.latest)
        analyzed: List[AnalyzeItem] = []
        for r in rows:
            url = r.get("url","")
            kind = r.get("kind","")
            barrier = r.get("barrier")
            text = r.get("excerpt") or r.get("raw_excerpt") or ""
            a = authority_score(url)
            l = logic_score(text)
            v = verdict(a, l, bool(barrier))
            analyzed.append(AnalyzeItem(
                rid=r.get("rid",""),
                time=r.get("time",""),
                url=url,
                kind=kind,
                authority=a,
                logic=l,
                verdict=v,
                barrier=barrier,
            ))
        # Hüküm özeti
        senedli = [x for x in analyzed if x.verdict == "SENEDLI_HABER"]
        supheli = [x for x in analyzed if x.verdict == "SUPHELI_IDDIA"]
        fasit = [x for x in analyzed if x.verdict == "FASIT_HABER"]
        manual = [x for x in analyzed if x.verdict == "MANUEL_MUDAHALE"]

        summary = (
            f"HÜKÜM: Senedli={len(senedli)}, Şüpheli={len(supheli)}, Fasıt={len(fasit)}, Manuel Müdahale={len(manual)}.\n"
            f"İlke: Senedsiz hüküm verilmez. Engel görülürse raporlanır."
        )
        out = ReportResponse(ok=True, time=__import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
                             summary=summary, items=analyzed)

        # içtihat kaydı
        store.put_case({
            "time": out.time,
            "type": "RAPOR",
            "summary": out.summary,
            "top": [{"rid": i.rid, "verdict": i.verdict, "authority": i.authority, "logic": i.logic, "url": i.url} for i in analyzed[:20]],
        })
        return out

    @app.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest):
        # Delil havuzu: son N kayıt ve/veya rapor içtihatları
        rows = store.latest(req.latest)
        evidence_rids = [r.get("rid","") for r in rows if r.get("rid")][:20]
        # Senedli özet: kullanıcı mesajına cevap verirken delile dayan
        # Eğer Ollama yoksa: deterministik/kurallı cevap
        evidence_brief = []
        for r in rows[:10]:
            if r.get("kind") == "rss":
                titles = [it.get("title","") for it in (r.get("items") or [])[:5]]
                evidence_brief.append(f"- RSS {r.get('url')}: " + "; ".join([t for t in titles if t][:5]))
            else:
                title = r.get("title") or ""
                evidence_brief.append(f"- PAGE {r.get('url')}: {title}".strip())

        system = SYSTEM + "\nKANIT ÖZETİ:\n" + "\n".join(evidence_brief[:10])
        user = req.message.strip()

        if llm.available():
            try:
                ans = llm.generate(system, user)
            except Exception:
                ans = (
                    "HÜKÜM: LLM katmanında geçici sorun.\n"
                    "Senedli Mod: Kanıt arşivi hazır. /report ile hüküm üretilebilir."
                )
        else:
            # LLM yoksa: basit senedli cevap
            ans = (
                "HÜKÜM: Yerel LLM erişilebilir değil.\n"
                "Senedli Mod aktif: Kanıtlar arşivde. /report çıktısı üzerinden hüküm verilir."
            )

        # chat içtihat kaydı
        store.put_case({
            "time": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
            "type": "CHAT",
            "question": user,
            "answer": ans,
            "evidence_rids": evidence_rids[:20],
        })

        return ChatResponse(ok=True, time=__import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
                            answer=ans, evidence_rids=evidence_rids[:20])

    return app
