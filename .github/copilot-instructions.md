# GitHub Copilot Repository Instructions for GitSéance (GitSeance)

You are assisting with development on **GitSéance (GitSeance)**: an Open-Source AI Code Necromancer that brings abandoned GitHub repositories back to life and predicts which files are about to die next. Built for **Hacktoberfest Open-Source AI Challenge: Week 4 ("Ghost in the Machine")**.

---

## 1. Project Philosophy & Core Commandments

When suggesting code, refactoring agents, or generating tests for GitSéance, strictly adhere to these core principles:

1. **The Four Specialized Agents Architecture**:
   - **💀 The Reaper (`backend/agents/reaper.py`)**: Traverses Git trees and commit blame history. Extracts file metrics, detects ghost fear comments (`do not touch`, `black magic`, `hack`, `nobody knows why`), and classifies haunting states (`dead`, `haunted`, `orphaned`, `cursed`, `fading`, `alive`).
   - **📊 The Oracle (`backend/agents/oracle.py` + `backend/services/tabpfn_client.py`)**: Uses **Prior Labs TabPFN-3.5** (Foundation Model for Tabular Data) to predict Code Mortality Risk (0.0 to 1.0) from a 7-dimensional git telemetry feature vector.
   - **🔮 The Medium (`backend/agents/medium.py` + `backend/services/gemma_client.py`)**: Uses **Google Gemma 3 / Gemini** open-weight LLM to channel the first-person persona of the deceased/departed author, extracting design constraints, regrets, and actionable Revival Blueprints.
   - **🔍 The Searcher (`backend/agents/searcher.py` + `backend/services/serpapi_client.py`)**: Uses **SerpApi** for real-time web search grounding to find contemporary 2026 drop-in library replacements and active CVE vulnerability advisories.

2. **Bulletproof Fallback Supremacy (Never Fail on Missing Keys)**:
   - The application must **never crash** if an external API key is absent or rate-limited.
   - If Google AI key is absent: `GemmaClient` falls back to `_fallback_channeling()` with structured, atmospheric developer ghosts.
   - If TabPFN key is absent: `TabPFNClient` falls back to calibrated Bayesian heuristic scoring.
   - If ElevenLabs key is absent: `GhostVoicePlayer` in `frontend/js/audio.js` seamlessly falls back to browser native `window.speechSynthesis` with eerie lowered pitch.
   - If SerpApi key is absent: `SerpApiClient` utilizes the built-in curated 2026 replacement knowledge base.
   - If GitHub rate limit is exceeded: `ReaperAgent` provides pre-computed forensic snapshots for historic graveyards (`flask-cache`, `jquery-color`).

3. **Non-Destructive Necromancy**:
   - GitSéance observes, diagnoses, and channels. It **never mutates** target repositories or deletes files.
   - All remediation advice is output as structured `RevivalPatch` blueprints, markdown dossiers, or JSON ledgers.

4. **Zero-Bloat Haunted CRT Aesthetic**:
   - The frontend is strictly **vanilla HTML5, CSS3, and modern ES6+ JavaScript**.
   - No heavy Node compilation steps, React, or Tailwind build chains.
   - Authentic retro CRT physics: phosphor glow, scanlines, mechanical keystroke synthesis (Web Audio API), and ectoplasmic particle systems.

---

## 2. Technology Stack & Coding Standards

- **Language**: Python 3.11+ using modern type annotations (`list[str]`, `dict[str, Any]`, `str | None`).
- **Web Framework**: FastAPI with asynchronous endpoints and Server-Sent Events (SSE) streaming (`StreamingResponse`).
- **Data Validation**: Pydantic v2 schemas (`backend/models/schemas.py`).
- **HTTP Transport**: `httpx.AsyncClient` with custom timeouts and structured error handling.
- **Frontend Stack**: Pure HTML5, CSS custom properties (variables), Web Audio API, Canvas 2D, and Server-Sent Events (`EventSource`).
- **Testing**: `pytest` with 100% pass requirement on `backend/tests/`.

---

## 3. Data Models & Schemas (`backend/models/schemas.py`)

- **`HauntingStatus`**: `dead` (2+ yrs untouched), `haunted` (fear comments / sole author left), `orphaned` (single author), `cursed` (high bug ratio), `fading` (declining churn), `alive` (active).
- **`FileMetrics`**: Granular git commit metrics (`days_since_last_commit`, `total_commits`, `unique_authors`, `bug_fix_commit_ratio`, `lines_added`, `lines_deleted`, `has_tests`, `churn_velocity`).
- **`HauntingReport`**: Comprehensive necropsy report for an inspected file.
- **`GhostChanneling`**: Gemma's first-person channeled transmission (`ghost_message`, `why_written`, `last_wish`, `revival_patch`).
- **`DependencyReplacement`**: Modern 2026 replacement package from SerpApi.

---

## 4. Prior Labs TabPFN-3.5 Feature Vector Specification

When engineering or adjusting features for The Oracle agent, maintain the 7-dimensional feature matrix:
1. `days_since_last_commit` (float): Days since most recent git commit.
2. `total_commits` (float): Total lifetime commit count touching the file.
3. `unique_authors` (float): Bus factor indicator (number of distinct committers).
4. `bug_fix_commit_ratio` (float): Ratio of commits containing bug-fix keywords (`fix`, `bug`, `patch`, `hotfix`).
5. `lines_ratio` (float): Ratio of additions to deletions `(lines_added + 1) / (lines_deleted + 1)`.
6. `has_tests` (float: 0.0 or 1.0): Binary indicator if file has corresponding test files.
7. `churn_velocity` (float): Frequency of changes per month.

---

## 5. Reusable Copilot Prompts

This repository provides reusable Copilot Prompt Templates in `.github/prompts/`:
- **`/resurrect-file`** (`.github/prompts/resurrect-file.prompt.md`): Guide Copilot to channel a legacy file and write a 2026 modernization patch.
- **`/tabpfn-mortality`** (`.github/prompts/tabpfn-mortality.prompt.md`): Guide Copilot to extract git metrics and calculate TabPFN mortality probability.
- **`/dep-modernize`** (`.github/prompts/dep-modernize.prompt.md`): Guide Copilot to audit deprecated packages and find drop-in replacements with CVE analysis.

---

## 6. Pre-Commit Verification Checklist

Before committing changes:
1. Run `python -m pytest backend/tests -v` to ensure all 23+ unit and integration tests pass.
2. Ensure no hardcoded secrets or API keys are committed (enforced by `.gitignore`).
3. Verify that all async routes handle timeouts and missing API keys gracefully.

