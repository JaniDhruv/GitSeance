"""
TabPFN Client — Prior Labs API for the Oracle agent's mortality prediction.
Uses the TabPFN API (not the pip package) to save Render storage.
"""

import httpx
import csv
import io
import sentry_sdk
from typing import Optional

from config import get_settings


class TabPFNClient:
    """Client for TabPFN API — tabular prediction for code mortality."""

    BASE_URL = "https://tabpfn.priorlabs.ai"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.tabpfn_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @sentry_sdk.trace
    async def predict_mortality(self, file_metrics: list[dict]) -> list[dict]:
        """
        Predict mortality risk for files using TabPFN API.

        Each file_metrics dict should contain:
        - days_since_last_commit (int)
        - total_commits (int)
        - unique_authors (int)
        - bug_fix_commit_ratio (float)
        - lines_ratio (float) — added/deleted ratio
        - has_tests (0 or 1)
        - churn_velocity (float)

        Returns list of dicts with file_path and mortality_risk (0.0 to 1.0).
        """

        if not self.api_key or not file_metrics:
            # Fallback: use heuristic scoring when API is unavailable
            return self._heuristic_mortality(file_metrics)

        # Build training data from the files themselves:
        # Files that haven't been touched in 540+ days are labeled "dead" (1)
        # Files touched within 180 days are labeled "alive" (0)
        # The rest are what we want to predict
        train_x = []
        train_y = []
        predict_x = []
        predict_indices = []

        feature_keys = [
            "days_since_last_commit",
            "total_commits",
            "unique_authors",
            "bug_fix_commit_ratio",
            "lines_ratio",
            "has_tests",
            "churn_velocity",
        ]

        for i, m in enumerate(file_metrics):
            features = [float(m.get(k, 0)) for k in feature_keys]
            days = m.get("days_since_last_commit", 9999)

            if days >= 540:
                train_x.append(features)
                train_y.append(1)  # dead
            elif days <= 180:
                train_x.append(features)
                train_y.append(0)  # alive
            else:
                # Both train with label and predict
                train_x.append(features)
                train_y.append(1 if days > 365 else 0)

            predict_x.append(features)
            predict_indices.append(i)

        # Need at least 2 classes to train
        if len(set(train_y)) < 2:
            return self._heuristic_mortality(file_metrics)

        try:
            payload = {
                "train_x": train_x,
                "train_y": train_y,
                "test_x": predict_x,
                "task_type": "classification",
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/predict",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

            # Extract probabilities for class 1 (dead)
            probabilities = result.get("probabilities", result.get("predictions", []))

            results = []
            for i, m in enumerate(file_metrics):
                if i < len(probabilities):
                    prob = probabilities[i]
                    # If prob is a list [prob_alive, prob_dead], take prob_dead
                    if isinstance(prob, list) and len(prob) >= 2:
                        mortality = float(prob[1])
                    else:
                        mortality = float(prob)
                else:
                    mortality = self._single_heuristic(m)

                results.append({
                    "file_path": m.get("file_path", f"file_{i}"),
                    "mortality_risk": round(min(max(mortality, 0.0), 1.0), 3),
                })

            return results

        except Exception as e:
            sentry_sdk.capture_exception(e)
            # Fallback to heuristic
            return self._heuristic_mortality(file_metrics)

    def _heuristic_mortality(self, file_metrics: list[dict]) -> list[dict]:
        """Fallback heuristic mortality scoring when TabPFN API is unavailable."""
        return [
            {
                "file_path": m.get("file_path", f"file_{i}"),
                "mortality_risk": round(self._single_heuristic(m), 3),
            }
            for i, m in enumerate(file_metrics)
        ]

    @staticmethod
    def _single_heuristic(m: dict) -> float:
        """Calculate a heuristic mortality score for a single file."""
        score = 0.0
        days = m.get("days_since_last_commit", 0)

        # Age is the strongest signal
        if days > 730:
            score += 0.5
        elif days > 365:
            score += 0.35
        elif days > 180:
            score += 0.2
        elif days > 90:
            score += 0.1

        # Single author = bus factor risk
        if m.get("unique_authors", 1) <= 1:
            score += 0.15

        # Low commit count = less maintained
        if m.get("total_commits", 0) <= 3:
            score += 0.1

        # High bug fix ratio = troubled code
        if m.get("bug_fix_commit_ratio", 0) > 0.5:
            score += 0.1

        # No tests = risky
        if not m.get("has_tests", False):
            score += 0.05

        # Low churn = stagnant
        if m.get("churn_velocity", 0) < 0.1:
            score += 0.1

        return min(score, 1.0)
