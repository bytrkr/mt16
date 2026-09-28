from __future__ import annotations
from mt16.core.types import ContentPacket, Domain, RiskLevel

NAME = "finance"

def run(query: str) -> ContentPacket:
    # Basit demo: finansal analiz iskeleti
    content = (
        f"Finance analysis: {query}. "
        "Consider cashflow, leverage, volatility, and liquidity. "
        "If needed, suggest scenario/stress tests."
    )
    return ContentPacket(
        source="FINANCE",
        domain=Domain.FINANCE,
        risk=RiskLevel.MEDIUM,
        content=content,
        meta={
            "module": NAME,
            "confidence_score": 0.62,
            "authority_score": 0.62,
            "logic_score": 0.64,
        },
    )
