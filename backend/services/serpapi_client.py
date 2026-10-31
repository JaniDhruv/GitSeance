"""
SerpApi Client — Web search for the Searcher agent's dependency replacement lookup.
"""

import httpx
import sentry_sdk

from config import get_settings


class SerpApiClient:
    """Client for SerpApi — live web search for modern dependency replacements."""

    BASE_URL = "https://serpapi.com/search.json"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.serpapi_key

    @sentry_sdk.trace
    async def search_replacement(self, package_name: str, language: str = "") -> list[dict]:
        """Search for modern replacements for a deprecated/dead package."""

        query = f"{package_name} alternative replacement 2026"
        if language:
            query += f" {language}"

        results = await self._search(query)
        return self._parse_results(results, package_name)

    @sentry_sdk.trace
    async def search_cve(self, package_name: str) -> list[str]:
        """Search for known CVE vulnerabilities in a package."""

        query = f"{package_name} CVE vulnerability security advisory"
        results = await self._search(query)

        cves = []
        for r in results.get("organic_results", [])[:5]:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            if "CVE" in title.upper() or "CVE" in snippet.upper():
                cves.append(f"{title}: {snippet[:150]}")

        return cves

    async def _search(self, query: str) -> dict:
        """Execute a SerpApi search."""
        if not self.api_key:
            return {"organic_results": []}

        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google",
            "num": 5,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return {"organic_results": []}

    @staticmethod
    def _parse_results(data: dict, original_package: str) -> list[dict]:
        """Parse SerpApi results into structured replacement suggestions."""
        replacements = []

        for result in data.get("organic_results", [])[:5]:
            replacements.append({
                "old_package": original_package,
                "new_package": result.get("title", "Unknown")[:100],
                "reason": result.get("snippet", "")[:200],
                "url": result.get("link", ""),
            })

        return replacements
