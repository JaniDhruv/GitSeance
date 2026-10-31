import pytest
from agents.reaper import ReaperAgent
from models.schemas import FileMetrics, HauntingStatus


def test_is_scannable():
    assert ReaperAgent._is_scannable("src/app.py") is True
    assert ReaperAgent._is_scannable("frontend/index.js") is True
    assert ReaperAgent._is_scannable("Dockerfile") is True
    assert ReaperAgent._is_scannable("image.png") is False
    assert ReaperAgent._is_scannable("archive.zip") is False


def test_looks_like_test():
    assert ReaperAgent._looks_like_test("tests/test_api.py") is True
    assert ReaperAgent._looks_like_test("src/components/button.spec.ts") is True
    assert ReaperAgent._looks_like_test("src/main.py") is False


def test_classify_clinically_dead_file():
    reaper = ReaperAgent()
    metrics = FileMetrics(
        file_path="old/deprecated.py",
        days_since_last_commit=1000,
        total_commits=10,
        unique_authors=2,
        bug_fix_commit_ratio=0.2,
        lines_added=100,
        lines_deleted=50,
        has_tests=True,
        churn_velocity=0.01,
        last_author="OldDev",
        last_commit_date="2023-01-01T00:00:00Z",
        last_commit_message="legacy commit",
    )

    status, score, warnings = reaper._classify_file(metrics, "old/deprecated.py")
    assert status == HauntingStatus.DEAD
    assert score >= 0.7
    assert any("clinically dead" in w for w in warnings)


def test_classify_haunted_fear_comment():
    reaper = ReaperAgent()
    metrics = FileMetrics(
        file_path="src/magic.py",
        days_since_last_commit=100,
        total_commits=15,
        unique_authors=3,
        bug_fix_commit_ratio=0.1,
        lines_added=500,
        lines_deleted=100,
        has_tests=True,
        churn_velocity=0.5,
        last_author="Wizard",
        last_commit_date="2026-06-01T00:00:00Z",
        last_commit_message="black magic workaround",
    )

    status, score, warnings = reaper._classify_file(metrics, "src/magic.py", fear_comments=["black magic", "do not touch"])
    assert status == HauntingStatus.HAUNTED
    assert any("Fear comment detected" in w for w in warnings)


def test_classify_cursed_high_bug_ratio():
    reaper = ReaperAgent()
    metrics = FileMetrics(
        file_path="src/buggy.py",
        days_since_last_commit=50,
        total_commits=20,
        unique_authors=4,
        bug_fix_commit_ratio=0.75,
        lines_added=1000,
        lines_deleted=800,
        has_tests=True,
        churn_velocity=1.2,
        last_author="Firefighter",
        last_commit_date="2026-09-01T00:00:00Z",
        last_commit_message="patch another crash",
    )

    status, score, warnings = reaper._classify_file(metrics, "src/buggy.py")
    assert status == HauntingStatus.CURSED
    assert any("cursed code" in w for w in warnings)
