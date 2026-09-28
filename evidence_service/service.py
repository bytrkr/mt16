from .connectors.web import collect_from_web
from .connectors.internal import collect_internal

def collect_evidence(payload: dict) -> dict:
    evidence = []
    if payload.get("web"):
        evidence.extend(collect_from_web(payload["web"]))
    if payload.get("internal"):
        evidence.extend(collect_internal(payload["internal"]))

    return {
        "evidence": evidence
    }
