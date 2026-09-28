from __future__ import annotations
from mt16.core.types import ContentPacket, Domain, RiskLevel

NAME = "sentiment"

def run(query: str) -> ContentPacket:
    # Demo sentiment pulse (0..1)
    pulse = 0.72
    anomaly = False
    content = f"Sentiment pulse: {pulse:.2f}. " + ("Anomaly detected." if anomaly else "No anomaly.")
    return ContentPacket(
        source="SENTIMENT",
        domain=Domain.SENTIMENT,
        risk=RiskLevel.LOW,
        content=content,
        meta={
            "module": NAME,
            "pulse_score": pulse,
            "anomaly": anomaly,
            "confidence_score": 0.58,
            "authority_score": 0.58,
            "logic_score": 0.58,
        },
    )
