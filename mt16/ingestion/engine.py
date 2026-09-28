import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

class IngestionEngine:
    def __init__(self):
        self.headers = {'User-Agent': 'MT16-Intelligence-Core/1.8 (Sovereign System)'}

    def scout(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            # Duvar Kontrolü (Bizans Engeli)
            if response.status_code in [401, 403, 429] or "captcha" in response.text.lower():
                return {"status": "MANUEL MÜDAHALE GEREKİYOR", "reason": "Erişim Engeli", "url": url}
            
            return {"status": "Success", "content": response.text, "url": url}
        except Exception as e:
            return {"status": "DEFERRED", "reason": str(e), "url": url}

    def fetch_rss(self, url):
        feed = feedparser.parse(url)
        return [{"source": url, "title": e.title, "link": e.link} for e in feed.entries]