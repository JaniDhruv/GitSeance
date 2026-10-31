import pytest
from datetime import datetime, timezone
from services.github_client import GitHubClient


def test_parse_repo_url():
    # Full HTTPS URL
    owner, repo = GitHubClient.parse_repo_url("https://github.com/mitsuhiko/flask-cache")
    assert owner == "mitsuhiko"
    assert repo == "flask-cache"

    # With .git suffix
    owner, repo = GitHubClient.parse_repo_url("https://github.com/mitsuhiko/flask-cache.git")
    assert owner == "mitsuhiko"
    assert repo == "flask-cache"

    # Short form
    owner, repo = GitHubClient.parse_repo_url("jquery/jquery-color")
    assert owner == "jquery"
    assert repo == "jquery-color"

    # Invalid URL raises ValueError
    with pytest.raises(ValueError):
        GitHubClient.parse_repo_url("invalid-url-string")


def test_extract_commit_stats_empty():
    stats = GitHubClient.extract_commit_stats([])
    assert stats["total_commits"] == 0
    assert stats["unique_authors"] == 0
    assert stats["bug_fix_ratio"] == 0.0


def test_extract_commit_stats_with_data():
    sample_commits = [
        {
            "commit": {
                "author": {"name": "Alice"},
                "committer": {"date": "2026-01-15T12:00:00Z"},
                "message": "fix critical memory leak and bug",
            }
        },
        {
            "commit": {
                "author": {"name": "Bob"},
                "committer": {"date": "2025-12-01T10:00:00Z"},
                "message": "initial feature implementation",
            }
        },
    ]

    stats = GitHubClient.extract_commit_stats(sample_commits)
    assert stats["total_commits"] == 2
    assert stats["unique_authors"] == 2
    assert stats["bug_fix_ratio"] == 0.5  # 1 of 2 commits has "fix" & "bug"
    assert stats["last_author"] == "Alice"
