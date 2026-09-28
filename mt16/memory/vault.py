import json
from pathlib import Path

class MemoryVault:
    def __init__(self):
        self.root = Path("./mt16/memory")

    def archive(self, data):
        date_path = self.root / datetime.now().strftime("%Y/%m/%d")
        date_path.mkdir(parents=True, exist_ok=True)
        filename = f"{hashlib.md5(data['url'].encode()).hexdigest()}.json"
        
        with open(date_path / filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return str(date_path / filename)