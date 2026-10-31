"""
SerpApi Client — Web search for the Searcher agent's dependency replacement lookup.
"""

import httpx
import sentry_sdk

from config import get_settings


CURATED_REPLACEMENTS = {
    "flask-cache": {
        "new_package": "Flask-Caching",
        "reason": "Active community fork of Flask-Cache supporting Python 3.11+, Redis, Memcached, and async views.",
        "url": "https://github.com/pallets-eco/flask-caching",
    },
    "flask_cache": {
        "new_package": "Flask-Caching",
        "reason": "Active community fork of Flask-Cache supporting Python 3.11+, Redis, Memcached, and async views.",
        "url": "https://github.com/pallets-eco/flask-caching",
    },
    "urllib2": {
        "new_package": "httpx",
        "reason": "Next-generation HTTP client for Python 3 with async support, HTTP/2, and type safety.",
        "url": "https://www.python-httpx.org",
    },
    "moment": {
        "new_package": "dayjs",
        "reason": "Fast 2KB alternative to Moment.js with the same modern API and immutable date chains.",
        "url": "https://day.js.org",
    },
    "request": {
        "new_package": "axios",
        "reason": "Promise-based HTTP client for the browser and node.js, replacing deprecated request.",
        "url": "https://axios-http.com",
    },
    "nose": {
        "new_package": "pytest",
        "reason": "Mature and modern test framework with powerful fixtures, plugins, and test discovery.",
        "url": "https://docs.pytest.org",
    },
    "pycrypto": {
        "new_package": "cryptography",
        "reason": "Cryptographic recipes and primitives for Python developers, replacing vulnerable PyCrypto.",
        "url": "https://cryptography.io",
    },
    "jquery-color": {
        "new_package": "colord",
        "reason": "Tiny 1.7KB color manipulation library with zero dependencies and TypeScript definitions.",
        "url": "https://github.com/omgovich/colord",
    },
    "jquery.color": {
        "new_package": "colord",
        "reason": "Tiny 1.7KB color manipulation library with zero dependencies and TypeScript definitions.",
        "url": "https://github.com/omgovich/colord",
    },
}


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
        parsed = self._parse_results(results, package_name)

        # Fallback to curated knowledge base if SerpApi yielded nothing
        if not parsed:
            clean_pkg = package_name.lower().replace("_", "-")
            if clean_pkg in CURATED_REPLACEMENTS:
                entry = CURATED_REPLACEMENTS[clean_pkg]
                parsed.append({
                    "old_package": package_name,
                    "new_package": entry["new_package"],
                    "reason": entry["reason"],
                    "url": entry["url"],
                })

        return parsed

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
