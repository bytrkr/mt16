# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Any
from mt16.core.types import Domain, RiskLevel, ModuleResult, ContentPacket


def run(packet: ContentPacket) -> ModuleResult:
    q = packet.query.lower()
    # Guardrails: not a safety policy for OpenAI, but MT16's internal risk gating
    score = 0.25
    if any(k in q for k in ["acil", "kritik", "hack", "patlat", "silah", "şiddet"]):
        score = 0.85
    risk = RiskLevel.HIGH if score >= 0.75 else (RiskLevel.MEDIUM if score >= 0.45 else RiskLevel.LOW)
    out: Dict[str, Any] = {"risk_score": score, "flags": []}
    if risk != RiskLevel.LOW:
        out["flags"].append("elevated_risk_language")
    summary = f"Risk Guard: risk_score={score:.2f} -> {risk.value}"
    return ModuleResult(
        name="risk_guard",
        domain=Domain.RISK,
        risk_level=risk,
        confidence=0.7,
        output=out,
        summary=summary,
    )
