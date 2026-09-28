from __future__ import annotations
import os, json, hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def stable_hash_record(record: Dict[str, Any]) -> str:
    b = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_hex(b)

def write_json(path: str, obj: Any) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)

def read_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def append_index(index_path: str, item: Dict[str, Any]) -> None:
    data = read_json(index_path, {"items": []})
    if "items" not in data or not isinstance(data["items"], list):
        data = {"items": []}
    data["items"].append(item)
    write_json(index_path, data)

def list_index(index_path: str) -> List[Dict[str, Any]]:
    data = read_json(index_path, {"items": []})
    items = data.get("items", [])
    return items if isinstance(items, list) else []
