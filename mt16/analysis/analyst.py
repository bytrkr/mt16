import hashlib

class SenedAnalyst:
    def evaluate(self, content, source_type):
        # Mizan-ı Hakikat: Kaynağın makamına ve içeriğin mantığına göre skorlama
        authority_score = 85 if source_type in ['official', 'financial_report'] else 40
        logic_score = 70 # LLM muhakemesi burada devreye girer
        
        status = "SENEDLİ" if (authority_score + logic_score) / 2 > 65 else "FÂSIT HABER"
        evidence_hash = hashlib.sha256(content.encode()).hexdigest()
        
        return {
            "authority_score": authority_score,
            "logic_score": logic_score,
            "status": status,
            "hash": evidence_hash,
            "timestamp": str(datetime.now())
        }