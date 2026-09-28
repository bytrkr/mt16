from mt16.core.types import RiskLevel, Domain

def assess_risk(topic: str, domain: Domain) -> RiskLevel:
    sensitive_keywords = [
        "kesin", "garanti", "mucize", "hemen", "şimdi al"
    ]
    if any(k in topic.lower() for k in sensitive_keywords):
        return RiskLevel.HIGH

    if domain in (Domain.MEDICAL, Domain.FINANCE):
        return RiskLevel.MEDIUM

    return RiskLevel.LOW

def allow_publish(risk: RiskLevel, human_approved: bool) -> bool:
    if risk == RiskLevel.HIGH:
        return False
    if risk == RiskLevel.MEDIUM and not human_approved:
        return False
    return True
