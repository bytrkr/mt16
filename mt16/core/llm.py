from __future__ import annotations

import os
import json
import requests
from typing import Any, Dict, Optional

def env_get(name: str, default: str="") -> str:
    v = os.environ.get(name)
    return v if v and v.strip() else default

class LocalLLM:
    def __init__(self, base_url: str, model: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def available(self) -> bool:
        try:
            r = requests.get(self.base_url + "/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def generate(self, system: str, user: str) -> str:
        # Ollama /api/generate
        payload = {
            "model": self.model,
            "prompt": f"{system}\n\nKULLANICI: {user}\nYANIT:",
            "stream": False,
        }
        r = requests.post(self.base_url + "/api/generate", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return (data.get("response") or "").strip()
