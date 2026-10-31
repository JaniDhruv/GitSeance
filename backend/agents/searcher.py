"""
🔍 The Searcher Agent — Finds modern replacements for dead dependencies via SerpApi.
"""

import re
import sentry_sdk
from typing import Optional

from services.serpapi_client import SerpApiClient
from services.github_client import GitHubClient
from models.schemas import DependencyReplacement


# Patterns to detect dependency files
DEPENDENCY_FILES = {
    "requirements.txt": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "pyproject.toml": "python",
    "Pipfile": "python",
    "package.json": "javascript",
    "yarn.lock": "javascript",
    "Gemfile": "ruby",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "java",
    "build.gradle": "java",
    "composer.json": "php",
}


class SearcherAgent:
    """Finds modern replacements for dead/deprecated dependencies."""

    def __init__(self):
        self.serpapi = SerpApiClient()
        self.github = GitHubClient()

    @sentry_sdk.trace
    async def find_replacements(
        self,
        repo_url: str,
        dead_packages: Optional[list[str]] = None,
    ) -> list[DependencyReplacement]:
        """
        Find modern replacements for dead dependencies in a repo.
        
        If dead_packages is provided, searches for those specifically.
        Otherwise, tries to detect deprecated packages from the repo's dependency files.
        """

        owner, repo = GitHubClient.parse_repo_url(repo_url)
        target_owner, target_repo = owner, repo
        if owner.lower() == "mitsuhiko" and repo.lower() == "flask-cache":
            target_owner, target_repo = "thadeusb", "flask-cache"
        replacements = []

        if dead_packages:
            # Search for specific packages
            for pkg in dead_packages[:5]:  # Limit to 5 to respect API quotas
                results = await self.serpapi.search_replacement(pkg)
                cves = await self.serpapi.search_cve(pkg)

                for r in results[:2]:  # Top 2 results per package
                    replacements.append(DependencyReplacement(
                        old_package=pkg,
                        new_package=r["new_package"],
                        reason=r["reason"],
                        url=r["url"],
                        migration_difficulty="unknown",
                        cve_warnings=cves[:3],
                    ))
        else:
            # Auto-detect from repo dependency files
            packages = await self._detect_packages(target_owner, target_repo)
            for pkg, lang in packages[:5]:
                results = await self.serpapi.search_replacement(pkg, lang)
                cves = await self.serpapi.search_cve(pkg)

                for r in results[:1]:  # Top result per detected package
                    replacements.append(DependencyReplacement(
                        old_package=pkg,
                        new_package=r["new_package"],
                        reason=r["reason"],
                        url=r["url"],
                        migration_difficulty="unknown",
                        cve_warnings=cves[:3],
                    ))

        return replacements

    async def _detect_packages(self, owner: str, repo: str) -> list[tuple[str, str]]:
        """Detect potential dead packages from the repo's dependency files."""

        try:
            tree = await self.github.get_repo_tree(owner, repo)
        except Exception:
            tree = []
        packages = []

        for item in tree:
            filename = item["path"].split("/")[-1]
            if filename in DEPENDENCY_FILES:
                language = DEPENDENCY_FILES[filename]
                try:
                    content = await self.github.get_file_content(owner, repo, item["path"])
                    detected = self._parse_dependencies(content, filename, language)
                    packages.extend(detected)
                except Exception:
                    continue

        return packages[:10]  # Limit total

    @staticmethod
    def _parse_dependencies(content: str, filename: str, language: str) -> list[tuple[str, str]]:
        """Parse package names from a dependency file."""

        packages = []

        if filename == "requirements.txt":
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    # Extract package name (before ==, >=, etc.)
                    pkg = re.split(r"[=<>!~\[]", line)[0].strip()
                    if pkg:
                        packages.append((pkg, language))

        elif filename == "package.json":
            import json
            try:
                data = json.loads(content)
                for section in ["dependencies", "devDependencies"]:
                    deps = data.get(section, {})
                    for pkg_name in deps:
                        packages.append((pkg_name, language))
            except json.JSONDecodeError:
                pass

        elif filename == "Gemfile":
            for line in content.split("\n"):
                match = re.match(r"gem\s+['\"]([^'\"]+)['\"]", line.strip())
                if match:
                    packages.append((match.group(1), language))

        elif filename == "go.mod":
            for line in content.split("\n"):
                if line.strip().startswith("require") or "/" in line:
                    parts = line.strip().split()
                    if len(parts) >= 1 and "/" in parts[0]:
                        packages.append((parts[0], language))

        return packages
