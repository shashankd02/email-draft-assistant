from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.core.config import settings


@dataclass
class SearchResult:
    citations: list[str]
    confidence: float
    provider: str


class SearchProvider:
    def search(self, query: str, recency_days: int = 7) -> SearchResult:
        raise NotImplementedError


class TavilySearchProvider(SearchProvider):
    def __init__(self) -> None:
        if not settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for Tavily provider")

    def search(self, query: str, recency_days: int = 7) -> SearchResult:
        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": settings.tavily_max_results,
            "include_answer": False,
            "days": recency_days,
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post("https://api.tavily.com/search", json=payload)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("results", [])
        citations = [item.get("url") for item in items if item.get("url")]
        raw_score = data.get("response_time")
        confidence = 0.8 if citations else 0.2
        _ = raw_score
        return SearchResult(citations=citations, confidence=confidence, provider="tavily")


class MockSearchProvider(SearchProvider):
    def search(self, query: str, recency_days: int = 7) -> SearchResult:
        _ = query
        _ = recency_days
        return SearchResult(citations=[], confidence=0.0, provider="mock")


def get_search_provider() -> SearchProvider:
    if settings.tavily_api_key:
        return TavilySearchProvider()
    return MockSearchProvider()
