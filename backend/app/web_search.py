from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import httpx


class DuckDuckGoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results: list[dict[str, str]] = []
        self.current: dict[str, str] | None = None
        self.capture: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "")

        if tag == "a" and "result__a" in classes:
            self.current = {"title": "", "url": clean_duckduckgo_url(attrs_dict.get("href", "")), "snippet": ""}
            self.capture = "title"
        elif tag == "a" and "result__snippet" in classes and self.current is not None:
            self.capture = "snippet"

    def handle_data(self, data: str):
        if self.current is not None and self.capture:
            self.current[self.capture] += data

    def handle_endtag(self, tag: str):
        if tag != "a" or self.current is None:
            return

        if self.capture == "snippet":
            self.current = clean_result(self.current)
            if self.current["title"] and self.current["url"]:
                self.results.append(self.current)
            self.current = None
        self.capture = None


async def web_search(query: str) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
    except httpx.HTTPError as error:
        return [f"Web search failed: {error}"]

    parser = DuckDuckGoParser()
    parser.feed(response.text)

    snippets = []
    for result in parser.results[:5]:
        snippets.append(f"{result['title']}\n{result['snippet']}\nSource: {result['url']}")

    return snippets or ["Web search ran, but no result snippets were found."]


def clean_duckduckgo_url(url: str) -> str:
    if not url:
        return ""
    url = unescape(url)
    if url.startswith("//"):
        url = f"https:{url}"

    parsed = urlparse(url)
    wrapped = parse_qs(parsed.query).get("uddg", [""])[0]
    return unquote(wrapped or url)


def clean_result(result: dict[str, str]) -> dict[str, str]:
    return {
        key: " ".join(unescape(value).split())
        for key, value in result.items()
    }
