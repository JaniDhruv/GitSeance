"""
GitHub API Client — Fetches commit history, blame, contributors, and repo metadata.
"""

import httpx
import re
import sentry_sdk
from datetime import datetime, timezone
from typing import Optional

from config import get_settings


class GitHubClient:
    """Async client for GitHub REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self):
        settings = get_settings()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.github_token:
            self.headers["Authorization"] = f"Bearer {settings.github_token}"

    @staticmethod
    def parse_repo_url(url: str) -> tuple[str, str]:
        """Extract owner and repo name from a GitHub URL."""
        # Handle: https://github.com/owner/repo, github.com/owner/repo, owner/repo
        patterns = [
            r"github\.com/([^/]+)/([^/\s?.#]+)",
            r"^([^/]+)/([^/\s]+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, url.strip().rstrip("/"))
            if match:
                return match.group(1), match.group(2).replace(".git", "")
        raise ValueError(f"Could not parse GitHub URL: {url}")

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict | list:
        """Make an authenticated GET request to GitHub API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self.headers,
                params=params or {},
            )
            response.raise_for_status()
            return response.json()

    @sentry_sdk.trace
    async def get_repo_info(self, owner: str, repo: str) -> dict:
        """Get repository metadata."""
        return await self._get(f"/repos/{owner}/{repo}")

    @sentry_sdk.trace
    async def get_repo_tree(self, owner: str, repo: str, branch: str = "main") -> list[dict]:
        """Get the full file tree of a repo (recursive)."""
        try:
            data = await self._get(
                f"/repos/{owner}/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
            )
        except httpx.HTTPStatusError:
            # Fallback to 'master' if 'main' doesn't exist
            data = await self._get(
                f"/repos/{owner}/{repo}/git/trees/master",
                params={"recursive": "1"},
            )
        # Filter to blobs (files) only, skip directories
        return [
            item for item in data.get("tree", [])
            if item["type"] == "blob"
        ]

    @sentry_sdk.trace
    async def get_file_commits(
        self, owner: str, repo: str, file_path: str, per_page: int = 30
    ) -> list[dict]:
        """Get commit history for a specific file."""
        return await self._get(
            f"/repos/{owner}/{repo}/commits",
            params={"path": file_path, "per_page": per_page},
        )

    @sentry_sdk.trace
    async def get_file_content(self, owner: str, repo: str, file_path: str) -> str:
        """Get the content of a file from the repo."""
        import base64
        data = await self._get(f"/repos/{owner}/{repo}/contents/{file_path}")
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return data.get("content", "")

    @sentry_sdk.trace
    async def get_contributors(self, owner: str, repo: str) -> list[dict]:
        """Get repository contributors with commit counts."""
        return await self._get(
            f"/repos/{owner}/{repo}/contributors",
            params={"per_page": 30},
        )

    @sentry_sdk.trace
    async def get_open_issues(self, owner: str, repo: str, per_page: int = 30) -> list[dict]:
        """Get open issues for the repo."""
        return await self._get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": "open", "per_page": per_page},
        )

    @sentry_sdk.trace
    async def get_languages(self, owner: str, repo: str) -> dict:
        """Get language breakdown of the repo."""
        return await self._get(f"/repos/{owner}/{repo}/languages")

    @staticmethod
    def compute_file_age_days(commits: list[dict]) -> int:
        """Compute days since the most recent commit touching a file."""
        if not commits:
            return 9999  # Unknown = very old

        latest = commits[0]
        date_str = latest.get("commit", {}).get("committer", {}).get("date", "")
        if not date_str:
            return 9999

        last_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - last_date).days

    @staticmethod
    def extract_commit_stats(commits: list[dict]) -> dict:
        """Extract useful statistics from a file's commit history."""
        if not commits:
            return {
                "total_commits": 0,
                "unique_authors": 0,
                "bug_fix_ratio": 0.0,
                "last_author": "unknown",
                "last_commit_date": "unknown",
                "last_commit_message": "",
                "churn_velocity": 0.0,
            }

        authors = set()
        bug_fix_keywords = {"fix", "bug", "patch", "hotfix", "repair", "resolve", "issue"}
        bug_fix_count = 0

        for commit in commits:
            author = commit.get("commit", {}).get("author", {}).get("name", "unknown")
            authors.add(author)

            message = commit.get("commit", {}).get("message", "").lower()
            if any(keyword in message for keyword in bug_fix_keywords):
                bug_fix_count += 1

        total = len(commits)
        latest = commits[0].get("commit", {})
        oldest = commits[-1].get("commit", {})

        # Calculate churn velocity (commits per month)
        latest_date_str = latest.get("committer", {}).get("date", "")
        oldest_date_str = oldest.get("committer", {}).get("date", "")
        churn_velocity = 0.0

        if latest_date_str and oldest_date_str:
            latest_date = datetime.fromisoformat(latest_date_str.replace("Z", "+00:00"))
            oldest_date = datetime.fromisoformat(oldest_date_str.replace("Z", "+00:00"))
            months = max((latest_date - oldest_date).days / 30.0, 1.0)
            churn_velocity = round(total / months, 2)

        return {
            "total_commits": total,
            "unique_authors": len(authors),
            "bug_fix_ratio": round(bug_fix_count / max(total, 1), 3),
            "last_author": latest.get("author", {}).get("name", "unknown"),
            "last_commit_date": latest_date_str,
            "last_commit_message": latest.get("message", "")[:200],
            "churn_velocity": churn_velocity,
        }
