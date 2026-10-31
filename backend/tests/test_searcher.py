import asyncio
from agents.searcher import SearcherAgent
from services.serpapi_client import SerpApiClient, CURATED_REPLACEMENTS


def test_parse_requirements_txt():
    content = """
# Legacy dependencies
flask-cache==0.13.1
urllib3>=1.26.0
pytest
-e .
"""
    packages = SearcherAgent._parse_dependencies(content, "requirements.txt", "python")
    pkg_names = [p[0] for p in packages]
    assert "flask-cache" in pkg_names
    assert "urllib3" in pkg_names
    assert "pytest" in pkg_names


def test_parse_package_json():
    content = """
{
  "name": "legacy-app",
  "dependencies": {
    "moment": "^2.29.1",
    "request": "^2.88.2"
  },
  "devDependencies": {
    "mocha": "^8.0.0"
  }
}
"""
    packages = SearcherAgent._parse_dependencies(content, "package.json", "javascript")
    pkg_names = [p[0] for p in packages]
    assert "moment" in pkg_names
    assert "request" in pkg_names
    assert "mocha" in pkg_names


def test_curated_replacements_fallback():
    async def _test():
        client = SerpApiClient()
        results = await client.search_replacement("flask-cache")
        assert len(results) > 0
        assert results[0]["new_package"] == "Flask-Caching"
        assert "pallets-eco" in results[0]["url"]

    asyncio.run(_test())
