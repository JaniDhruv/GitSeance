import pytest
from models.schemas import (
    HauntingStatus,
    FileMetrics,
    HauntingReport,
    RevivalPatch,
    GhostChanneling,
    SeanceRequest,
    ChannelRequest,
    TTSRequest,
    SeanceResponse,
)


def test_haunting_status_enum():
    assert HauntingStatus.DEAD == "dead"
    assert HauntingStatus.HAUNTED == "haunted"
    assert HauntingStatus.ORPHANED == "orphaned"
    assert HauntingStatus.CURSED == "cursed"
    assert HauntingStatus.FADING == "fading"
    assert HauntingStatus.ALIVE == "alive"


def test_file_metrics_and_haunting_report():
    metrics = FileMetrics(
        file_path="src/legacy.py",
        days_since_last_commit=800,
        total_commits=15,
        unique_authors=1,
        bug_fix_commit_ratio=0.6,
        lines_added=300,
        lines_deleted=100,
        has_tests=False,
        churn_velocity=0.05,
        last_author="GhostDev",
        last_commit_date="2024-01-01T00:00:00Z",
        last_commit_message="hack: do not touch",
    )
    assert metrics.file_path == "src/legacy.py"

    report = HauntingReport(
        file_path="src/legacy.py",
        status=HauntingStatus.DEAD,
        ghost_score=0.92,
        mortality_risk=0.88,
        metrics=metrics,
        warnings=["💀 Clinically dead", "👻 Fear comment"],
    )
    assert report.ghost_score == 0.92
    assert report.mortality_risk == 0.88
    assert len(report.warnings) == 2


def test_seance_request_validation():
    req = SeanceRequest(repo_url="https://github.com/pallets/flask")
    assert req.repo_url == "https://github.com/pallets/flask"

    with pytest.raises(Exception):
        SeanceRequest()
