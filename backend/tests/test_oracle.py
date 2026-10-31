import asyncio
from services.tabpfn_client import TabPFNClient
from agents.oracle import OracleAgent
from models.schemas import FileMetrics, HauntingReport, HauntingStatus


def test_tabpfn_single_heuristic():
    # Dead file metrics
    dead_metrics = {
        "days_since_last_commit": 900,
        "total_commits": 2,
        "unique_authors": 1,
        "bug_fix_commit_ratio": 0.6,
        "lines_ratio": 1.0,
        "has_tests": False,
        "churn_velocity": 0.0,
    }
    score = TabPFNClient._single_heuristic(dead_metrics)
    assert score >= 0.7

    # Healthy active file metrics
    active_metrics = {
        "days_since_last_commit": 10,
        "total_commits": 40,
        "unique_authors": 5,
        "bug_fix_commit_ratio": 0.1,
        "lines_ratio": 1.5,
        "has_tests": True,
        "churn_velocity": 2.5,
    }
    score = TabPFNClient._single_heuristic(active_metrics)
    assert score < 0.3


def test_oracle_enrich_reports():
    async def _test():
        oracle = OracleAgent()
        m1 = FileMetrics(
            file_path="old.py",
            days_since_last_commit=800,
            total_commits=1,
            unique_authors=1,
            bug_fix_commit_ratio=0.0,
            lines_added=10,
            lines_deleted=0,
            has_tests=False,
            churn_velocity=0.0,
            last_author="Solo",
            last_commit_date="",
            last_commit_message="",
        )
        r1 = HauntingReport(file_path="old.py", status=HauntingStatus.DEAD, ghost_score=0.9, mortality_risk=None, metrics=m1)

        enriched = await oracle.predict_mortality([r1])
        assert len(enriched) == 1
        assert enriched[0].mortality_risk is not None
        assert enriched[0].mortality_risk >= 0.5

    asyncio.run(_test())
