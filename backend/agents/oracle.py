"""
📊 The Oracle Agent — Predicts file mortality using TabPFN.
"""

import sentry_sdk

from services.tabpfn_client import TabPFNClient
from models.schemas import HauntingReport


class OracleAgent:
    """Uses TabPFN to predict which files are about to die."""

    def __init__(self):
        self.tabpfn = TabPFNClient()

    @sentry_sdk.trace
    async def predict_mortality(self, reports: list[HauntingReport]) -> list[HauntingReport]:
        """
        Enrich haunting reports with TabPFN mortality predictions.
        
        Takes the Reaper's output and adds mortality_risk scores
        using TabPFN's tabular classification.
        """

        if not reports:
            return reports

        # Convert reports to TabPFN feature format
        file_metrics = []
        for report in reports:
            m = report.metrics
            file_metrics.append({
                "file_path": m.file_path,
                "days_since_last_commit": m.days_since_last_commit,
                "total_commits": m.total_commits,
                "unique_authors": m.unique_authors,
                "bug_fix_commit_ratio": m.bug_fix_commit_ratio,
                "lines_ratio": (m.lines_added + 1) / (m.lines_deleted + 1),
                "has_tests": 1 if m.has_tests else 0,
                "churn_velocity": m.churn_velocity,
            })

        # Get TabPFN predictions
        predictions = await self.tabpfn.predict_mortality(file_metrics)

        # Map predictions back to reports
        pred_map = {p["file_path"]: p["mortality_risk"] for p in predictions}

        for report in reports:
            risk = pred_map.get(report.metrics.file_path)
            if risk is not None:
                report.mortality_risk = risk

        # Re-sort by mortality risk (highest first)
        reports.sort(
            key=lambda r: r.mortality_risk if r.mortality_risk is not None else r.ghost_score,
            reverse=True,
        )

        return reports
