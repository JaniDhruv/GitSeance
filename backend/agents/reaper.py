"""
💀 The Reaper Agent — Scans a GitHub repo and identifies dead/haunted files.
"""

import asyncio
import sentry_sdk
from typing import Optional

from services.github_client import GitHubClient
from models.schemas import FileMetrics, HauntingReport, HauntingStatus


# File extensions worth scanning (skip binaries, images, etc.)
SCANNABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".php", ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt",
    ".html", ".css", ".scss", ".less", ".vue", ".svelte",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".sql",
    ".sh", ".bash", ".zsh", ".ps1", ".bat",
    ".md", ".rst", ".txt",
    ".dockerfile", ".tf", ".hcl",
}

# Max files to scan (GitHub API rate limit protection)
MAX_FILES_TO_SCAN = 50

# Ghost comments that indicate haunted code
GHOST_COMMENTS = [
    "do not touch", "don't touch", "do not modify", "don't modify",
    "hack", "workaround", "fixme", "todo", "xxx", "temporary",
    "this is a mess", "god forgive me", "i'm sorry", "forgive me",
    "magic number", "black magic", "voodoo", "cursed",
    "nobody knows why", "don't ask", "here be dragons",
    "this should never happen", "pray this works",
]


class ReaperAgent:
    """Scans a repository and produces haunting reports for each file."""

    def __init__(self):
        self.github = GitHubClient()

    @sentry_sdk.trace
    async def scan_repository(self, repo_url: str) -> list[HauntingReport]:
        """Scan a GitHub repository and return haunting reports."""

        owner, repo = GitHubClient.parse_repo_url(repo_url)

        # Get the file tree
        tree = await self.github.get_repo_tree(owner, repo)

        # Filter to scannable files
        scannable_files = [
            item for item in tree
            if self._is_scannable(item["path"])
        ]

        # Limit to prevent API rate exhaustion
        scannable_files = scannable_files[:MAX_FILES_TO_SCAN]

        # Scan files concurrently (in batches to respect rate limits)
        reports = []
        batch_size = 8
        for i in range(0, len(scannable_files), batch_size):
            batch = scannable_files[i:i + batch_size]
            tasks = [
                self._scan_file(owner, repo, item["path"])
                for item in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, HauntingReport):
                    reports.append(result)
                elif isinstance(result, Exception):
                    sentry_sdk.capture_exception(result)

        # Sort by ghost score descending (most haunted first)
        reports.sort(key=lambda r: r.ghost_score, reverse=True)

        return reports

    async def _scan_file(self, owner: str, repo: str, file_path: str) -> HauntingReport:
        """Scan a single file and produce a haunting report."""

        # Get commit history for this file
        commits = await self.github.get_file_commits(owner, repo, file_path, per_page=20)

        # Compute metrics
        days_since = GitHubClient.compute_file_age_days(commits)
        stats = GitHubClient.extract_commit_stats(commits)

        metrics = FileMetrics(
            file_path=file_path,
            days_since_last_commit=days_since,
            total_commits=stats["total_commits"],
            unique_authors=stats["unique_authors"],
            bug_fix_commit_ratio=stats["bug_fix_ratio"],
            lines_added=0,  # Would need per-commit stats
            lines_deleted=0,
            has_tests=self._looks_like_test(file_path),
            churn_velocity=stats["churn_velocity"],
            last_author=stats["last_author"],
            last_commit_date=stats["last_commit_date"],
            last_commit_message=stats["last_commit_message"],
        )

        # Determine haunting status and ghost score
        status, ghost_score, warnings = self._classify_file(metrics, file_path)

        return HauntingReport(
            file_path=file_path,
            status=status,
            ghost_score=ghost_score,
            mortality_risk=None,  # Filled by Oracle agent later
            metrics=metrics,
            warnings=warnings,
        )

    def _classify_file(
        self, metrics: FileMetrics, file_path: str
    ) -> tuple[HauntingStatus, float, list[str]]:
        """Classify a file's haunting status based on its metrics."""

        warnings = []
        score = 0.0
        days = metrics.days_since_last_commit

        # ──── Age-based scoring ────
        if days >= 730:  # 2+ years
            score += 0.5
            warnings.append(f"💀 Last touched {days} days ago — clinically dead")
        elif days >= 365:
            score += 0.35
            warnings.append(f"👻 Last touched {days} days ago — fading fast")
        elif days >= 180:
            score += 0.2
            warnings.append(f"🌫️ Last touched {days} days ago — growing cold")
        elif days >= 90:
            score += 0.1

        # ──── Bus factor ────
        if metrics.unique_authors <= 1:
            score += 0.15
            warnings.append("🪦 Single author — orphan risk if they leave")

        # ──── Low activity ────
        if metrics.total_commits <= 2:
            score += 0.1
            warnings.append("⚰️ Barely any commit history")

        # ──── Bug-heavy ────
        if metrics.bug_fix_commit_ratio > 0.5:
            score += 0.1
            warnings.append("☠️ Over half the commits are bug fixes — cursed code")

        # ──── No tests ────
        if not metrics.has_tests and not self._looks_like_test(file_path):
            score += 0.05
            warnings.append("🕸️ No associated tests found")

        # ──── Stagnant churn ────
        if metrics.churn_velocity < 0.1 and days > 180:
            score += 0.1
            warnings.append("🧊 Zero churn — this code is frozen")

        # Clamp score
        score = min(score, 1.0)

        # Determine status
        if score >= 0.7:
            status = HauntingStatus.DEAD
        elif score >= 0.5:
            if metrics.unique_authors <= 1:
                status = HauntingStatus.ORPHANED
            else:
                status = HauntingStatus.HAUNTED
        elif score >= 0.3:
            status = HauntingStatus.FADING
        else:
            status = HauntingStatus.ALIVE

        # Check for cursed indicators
        if metrics.bug_fix_commit_ratio > 0.6:
            status = HauntingStatus.CURSED

        return status, round(score, 3), warnings

    @staticmethod
    def _is_scannable(file_path: str) -> bool:
        """Check if a file should be scanned based on extension."""
        import os
        _, ext = os.path.splitext(file_path.lower())
        if not ext:
            # Include extensionless files like Makefile, Dockerfile, Gemfile
            basename = os.path.basename(file_path).lower()
            return basename in {
                "makefile", "dockerfile", "gemfile", "rakefile",
                "procfile", "vagrantfile", "jenkinsfile",
            }
        return ext in SCANNABLE_EXTENSIONS

    @staticmethod
    def _looks_like_test(file_path: str) -> bool:
        """Heuristic: does this file path suggest it's a test?"""
        path_lower = file_path.lower()
        return any(indicator in path_lower for indicator in [
            "test", "spec", "__test__", "_test.", ".test.",
            "tests/", "spec/", "__tests__/",
        ])
