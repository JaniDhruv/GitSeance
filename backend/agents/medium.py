"""
🔮 The Medium Agent — Channels the ghost of a file's original author via Gemma.
"""

import sentry_sdk

from services.gemma_client import GemmaClient
from services.github_client import GitHubClient
from models.schemas import GhostChanneling, RevivalPatch


class MediumAgent:
    """Channels the ghost of the original developer using Gemma."""

    def __init__(self):
        self.gemma = GemmaClient()
        self.github = GitHubClient()

    @sentry_sdk.trace
    async def channel_file(
        self,
        repo_url: str,
        file_path: str,
        file_content: str | None = None,
    ) -> GhostChanneling:
        """
        Channel the ghost of a specific file's author.
        
        Gathers context from git history and feeds it to Gemma
        to produce a first-person ghost channeling.
        """

        owner, repo = GitHubClient.parse_repo_url(repo_url)

        # Get commit history for context
        commits = await self.github.get_file_commits(owner, repo, file_path, per_page=10)
        stats = GitHubClient.extract_commit_stats(commits)

        # Get file content if not provided
        if not file_content:
            try:
                file_content = await self.github.get_file_content(owner, repo, file_path)
            except Exception:
                file_content = "(File content could not be retrieved — the ghost's remains have decomposed)"

        # Build commit history context string
        commit_context = "\n".join(
            f"- [{c.get('commit', {}).get('committer', {}).get('date', 'unknown')}] "
            f"{c.get('commit', {}).get('author', {}).get('name', 'unknown')}: "
            f"{c.get('commit', {}).get('message', '')[:100]}"
            for c in commits[:10]
        )

        # Channel through Gemma
        result = await self.gemma.channel_ghost(
            file_path=file_path,
            file_content=file_content,
            commit_history=commit_context,
            last_author=stats["last_author"],
            last_date=stats["last_commit_date"],
            last_message=stats["last_commit_message"],
        )

        # Build structured response
        return GhostChanneling(
            ghost_message=result.get("ghost_message", "The spirits are silent..."),
            why_written=result.get("why_written", "The ghost could not be reached."),
            last_wish=result.get("last_wish", "I have no regrets... or so I tell myself."),
            revival_patch=RevivalPatch(
                summary=result.get("revival_summary", "Modernize and refactor."),
                migration_steps=result.get("migration_steps", ["Review the code", "Update dependencies"]),
                estimated_effort=result.get("effort_estimate", "moderate"),
            ),
        )
