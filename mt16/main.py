from __future__ import annotations
import os
from mt16.api.app import build_app

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = build_app(BASE_DIR)
