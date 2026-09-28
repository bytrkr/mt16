def collect_from_web(query: str):
    return [
        {"source": "web", "content": f"web evidence for {query}"}
    ]
