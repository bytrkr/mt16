def collect_internal(query: str):
    return [
        {"source": "internal", "content": f"internal evidence for {query}"}
    ]
