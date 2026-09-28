from uuid import uuid4
from typing import Dict, Any

from modules.audit.agent import AuditAgent
from modules.historical_reasoning.agent import HistoricalReasoningAgent
from modules.historical_reasoning.schema import HistoricalContext


class Orchestrator:
    """
    MT16 Core Orchestrator
    - Agent'ları sırayla çağırır
    - Karar vermez
    - Her adımı audit eder
    """

    def __init__(self) -> None:
        self.audit = AuditAgent()
        self.historical_reasoning = HistoricalReasoningAgent()

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        trace_id = str(uuid4())
        ctx = {"trace_id": trace_id}

        # 1️⃣ Historical reasoning (pasif sınıflandırma)
        historical_ctx = HistoricalContext(
            date=input_data.get("date"),
            geography=input_data.get("geography"),
            hints=input_data.get("hints"),
        )

        historical_result = self.historical_reasoning.run(historical_ctx)

        # 2️⃣ Audit
        self.audit.run(
            event_type="historical_reasoning",
            payload={
                "input": input_data,
                "output": {
                    "legal_system": historical_result.legal_system,
                    "confidence": historical_result.confidence,
                    "reasoning": historical_result.reasoning,
                },
            },
            ctx=ctx,
        )

        # 3️⃣ Orchestrator çıktısı (karar değil, durum)
        return {
            "trace_id": trace_id,
            "historical_legal_system": historical_result.legal_system,
            "confidence": historical_result.confidence,
            "reasoning": historical_result.reasoning,
        }
