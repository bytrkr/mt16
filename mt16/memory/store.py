from __future__ import annotations

import os
import json
import glob
import hashlib
import datetime as dt
from typing import Any, Dict, List, Optional

def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

class MemoryStore:
    def __init__(self, root: str):
        self.root = root
        ensure_dir(self.root)

    def put(self, record: Dict[str, Any]) -> str:
        # hash: url + time + kind + excerpt/titles
        seed = json.dumps({
            "url": record.get("url",""),
            "time": record.get("time",""),
            "kind": record.get("kind",""),
            "x": record.get("excerpt") or record.get("raw_excerpt") or ""
        }, ensure_ascii=False, sort_keys=True)
        rid = sha256_text(seed)
        record["rid"] = rid
        # tarihli dosya: YYYY-MM-DD.jsonl
        day = (record.get("time","")[:10] or now_iso()[:10])
        path = os.path.join(self.root, f"{day}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return rid

    def latest(self, n: int = 20) -> List[Dict[str, Any]]:
        files = sorted(glob.glob(os.path.join(self.root, "*.jsonl")), reverse=True)
        out: List[Dict[str, Any]] = []
        for fp in files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # sondan
                for ln in reversed(lines):
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        continue
                    if len(out) >= n:
                        return out
            except Exception:
                continue
        return out

    def put_case(self, case: Dict[str, Any]) -> str:
        # içtihat defteri
        ensure_dir(os.path.join(self.root, "case_law"))
        seed = json.dumps(case, ensure_ascii=False, sort_keys=True)
        cid = sha256_text(seed)
        case["cid"] = cid
        day = (case.get("time","")[:10] or now_iso()[:10])
        path = os.path.join(self.root, "case_law", f"{day}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
        return cid
