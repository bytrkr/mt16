from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class Domain(Enum):
    FINANCE = "finance"
    MEDICAL = "medical"
    SOCIAL = "social"
    GENERAL = "general"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ContentPacket:
    topic: str
    domain: Domain
    payload: Dict[str, Any]
    risk: RiskLevel
