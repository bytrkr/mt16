# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Any, List
from mt16.core.types import Domain, RiskLevel, ModuleResult, ContentPacket


def run(packet: ContentPacket) -> ModuleResult:
    # Generate 3 scenario variants (low/base/high stress)
    scenarios: List[Dict[str, Any]] = [
        {"name": "Base", "assumption": "Piyasa yatay/ılımlı", "impact": "Orta volatilite", "move": "Dengeli portföy"},
        {"name": "Stress", "assumption": "Likidite sıkışması / negatif haber", "impact": "Yüksek volatilite", "move": "Nakit + defansif"},
        {"name": "Opportunity", "assumption": "Pozitif sürpriz / risk iştahı", "impact": "Yükseliş", "move": "Kademeli alım"},
    ]
    out: Dict[str, Any] = {"scenarios": scenarios}
    summary = "Scenario Simulator: 3 varyant senaryo üretildi."
    return ModuleResult(
        name="scenario_simulator",
        domain=Domain.SCENARIO,
        risk_level=RiskLevel.MEDIUM,
        confidence=0.58,
        output=out,
        summary=summary,
    )
