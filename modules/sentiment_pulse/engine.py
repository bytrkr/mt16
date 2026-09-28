# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Any
from mt16.core.types import Domain, RiskLevel, ModuleResult, ContentPacket


def run(packet: ContentPacket) -> ModuleResult:
    q = packet.query.lower()
    mood = "neutral"
    if any(k in q for k in ["panik", "korku", "endişe", "kriz"]):
        mood = "anxious"
    if any(k in q for k in ["fırsat", "kazanç", "umut"]):
        mood = "optimistic"
    score = 0.52
    if mood == "anxious":
        score = 0.72
    elif mood == "optimistic":
        score = 0.62
    out: Dict[str, Any] = {"mood": mood, "sentiment_score": score}
    summary = f"Sentiment Pulse: mood={mood}, sentiment_score={score:.2f}"
    return ModuleResult(
        name="sentiment_pulse",
        domain=Domain.SENTIMENT,
        risk_level=RiskLevel.LOW,
        confidence=0.6,
        output=out,
        summary=summary,
    )
