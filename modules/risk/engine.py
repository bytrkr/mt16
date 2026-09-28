from __future__ import annotations
from mt16.core.types import ContentPacket, Domain, RiskLevel

NAME = "risk"

def run(query: str) -> ContentPacket:
    # Demo risk değerlendirmesi
    content = (
        "Risk assessment: general financial risks exist. "
        "Recommend scenario/stress testing and risk controls (limits, hedges, compliance)."
    )
    return ContentPacket(
        source="RISK",
        domain=Domain.RISK,
        risk=RiskLevel.MEDIUM,
        content=content,
        meta={
            "module": NAME,
            "confidence_score": 0.60,
            "authority_score": 0.60,
            "logic_score": 0.61,
        },
    )
