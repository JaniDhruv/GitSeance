from services.gemma_client import GemmaClient


def test_parse_channeling_structured_output():
    raw_response = """
---GHOST_MESSAGE---
I wander these abandoned lines, whispering warnings of ancient memory leaks.
---WHY_WRITTEN---
We had to support legacy Python 2 environments under severe memory caps.
---LAST_WISH---
I wish I had written comprehensive unit tests before moving on.
---REVIVAL_SUMMARY---
Rewrite using modern async syntax and type annotations.
---MIGRATION_STEPS---
1. Audit imports
2. Add type hints
3. Write pytest fixtures
---EFFORT_ESTIMATE---
moderate
"""
    parsed = GemmaClient._parse_channeling(raw_response)
    assert "whispering warnings" in parsed["ghost_message"]
    assert "legacy Python 2" in parsed["why_written"]
    assert "comprehensive unit tests" in parsed["last_wish"]
    assert "Rewrite using modern" in parsed["revival_summary"]
    assert len(parsed["migration_steps"]) == 3
    assert parsed["effort_estimate"] == "moderate"


def test_fallback_channeling():
    fallback = GemmaClient._fallback_channeling(
        file_path="src/legacy.py",
        last_author="Armin",
        last_date="2016-04-12",
        last_message="final release",
    )
    assert "Armin" in fallback["ghost_message"]
    assert "src/legacy.py" in fallback["ghost_message"]
    assert len(fallback["migration_steps"]) >= 3
    assert fallback["effort_estimate"] == "moderate"
