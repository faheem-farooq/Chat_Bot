import httpx


async def web_search(query: str) -> list[str]:
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
        )
        response.raise_for_status()
        data = response.json()

    snippets: list[str] = []
    abstract = data.get("AbstractText")
    if abstract:
        snippets.append(abstract)

    for topic in data.get("RelatedTopics", [])[:5]:
        text = topic.get("Text")
        if text:
            snippets.append(text)

    return snippets[:5] or ["No useful instant-answer web results were found."]

