"""
Séance Router — Main API endpoints for the GitSeance workflow.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import sentry_sdk
import json
import asyncio

from models.schemas import (
    SeanceRequest, SeanceResponse,
    ChannelRequest, ChannelResponse,
    HauntingStatus,
)
from agents.reaper import ReaperAgent
from agents.oracle import OracleAgent
from agents.medium import MediumAgent
from agents.searcher import SearcherAgent
from services.gemma_client import GemmaClient

router = APIRouter(prefix="/api/seance", tags=["seance"])

# Shared agent instances
reaper = ReaperAgent()
oracle = OracleAgent()
medium = MediumAgent()
searcher = SearcherAgent()
gemma = GemmaClient()


@router.post("/scan", response_model=SeanceResponse)
async def begin_seance(request: SeanceRequest):
    """
    Begin a séance: scan a GitHub repository for dead/haunted files.
    
    This runs the Reaper (dead file scan) and Oracle (mortality prediction)
    agents, returning a full haunting report.
    """

    with sentry_sdk.start_transaction(op="seance", name="begin_seance"):
        try:
            # Step 1: Reaper scans for dead files
            with sentry_sdk.start_span(op="agent", description="Reaper scan"):
                reports = await reaper.scan_repository(request.repo_url)

            if not reports:
                raise HTTPException(
                    status_code=404,
                    detail="No scannable files found in this repository. The graveyard is empty."
                )

            # Step 2: Oracle predicts mortality
            with sentry_sdk.start_span(op="agent", description="Oracle prediction"):
                reports = await oracle.predict_mortality(reports)

            # Step 3: Generate séance summary
            haunting_data = "\n".join(
                f"- {r.file_path}: status={r.status.value}, ghost_score={r.ghost_score}, "
                f"mortality_risk={r.mortality_risk}"
                for r in reports[:20]
            )

            with sentry_sdk.start_span(op="agent", description="Gemma summary"):
                summary = await gemma.generate_summary(
                    repo_name=request.repo_url.split("/")[-1],
                    haunting_data=haunting_data,
                )

            # Count statuses
            status_counts = {s: 0 for s in HauntingStatus}
            for r in reports:
                status_counts[r.status] += 1

            from services.github_client import GitHubClient
            _, repo_name = GitHubClient.parse_repo_url(request.repo_url)

            return SeanceResponse(
                repo_name=repo_name,
                repo_url=request.repo_url,
                total_files_scanned=len(reports),
                dead_count=status_counts[HauntingStatus.DEAD],
                haunted_count=status_counts[HauntingStatus.HAUNTED],
                orphaned_count=status_counts[HauntingStatus.ORPHANED],
                cursed_count=status_counts[HauntingStatus.CURSED],
                alive_count=status_counts[HauntingStatus.ALIVE]
                    + status_counts[HauntingStatus.FADING],
                haunting_reports=reports,
                summary=summary,
            )

        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise HTTPException(
                status_code=500,
                detail=f"The séance was disrupted: {str(e)}"
            )


@router.post("/channel", response_model=ChannelResponse)
async def channel_ghost(request: ChannelRequest):
    """
    Channel the ghost of a specific file's author.
    
    Runs the Medium (Gemma ghost channeling) and Searcher (SerpApi
    dependency replacement) agents for a specific file.
    """

    with sentry_sdk.start_transaction(op="seance", name="channel_ghost"):
        try:
            # Run Medium and Searcher concurrently
            with sentry_sdk.start_span(op="agent", description="Medium + Searcher"):
                channeling_task = medium.channel_file(
                    repo_url=request.repo_url,
                    file_path=request.file_path,
                    file_content=request.file_content,
                )
                replacements_task = searcher.find_replacements(
                    repo_url=request.repo_url,
                )

                channeling, replacements = await asyncio.gather(
                    channeling_task,
                    replacements_task,
                    return_exceptions=True,
                )

            # Handle exceptions from concurrent tasks
            if isinstance(channeling, Exception):
                sentry_sdk.capture_exception(channeling)
                raise HTTPException(
                    status_code=500,
                    detail=f"The Medium lost connection to the spirit realm: {str(channeling)}"
                )

            if isinstance(replacements, Exception):
                sentry_sdk.capture_exception(replacements)
                replacements = []  # Non-critical, proceed without replacements

            return ChannelResponse(
                file_path=request.file_path,
                channeling=channeling,
                replacements=replacements if isinstance(replacements, list) else [],
            )

        except HTTPException:
            raise
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise HTTPException(
                status_code=500,
                detail=f"The channeling was disrupted: {str(e)}"
            )


@router.get("/stream")
async def stream_seance(repo_url: str):
    """
    Stream live séance progress via Server-Sent Events (SSE).
    Sends real-time telemetry from Reaper, Oracle, and Gemma agents as the ritual unfolds.
    """

    async def event_generator():
        try:
            msg = json.dumps({"agent": "reaper", "message": f"Summoning repository spirits for {repo_url}..."})
            yield f"data: {msg}\n\n"
            await asyncio.sleep(0.05)

            # Step 1: Reaper
            msg = json.dumps({"agent": "reaper", "message": "Traversing git commit trees and blame history..."})
            yield f"data: {msg}\n\n"
            reports = await reaper.scan_repository(repo_url)
            msg = json.dumps({"agent": "reaper", "message": f"Reaper cataloged {len(reports)} files from the codebase graveyard."})
            yield f"data: {msg}\n\n"
            await asyncio.sleep(0.05)

            # Step 2: Oracle
            msg = json.dumps({"agent": "oracle", "message": "Synthesizing 7-dimensional feature vectors for TabPFN-3.5..."})
            yield f"data: {msg}\n\n"
            reports = await oracle.predict_mortality(reports)
            msg = json.dumps({"agent": "oracle", "message": "TabPFN Bayesian code mortality calculation complete."})
            yield f"data: {msg}\n\n"
            await asyncio.sleep(0.05)

            # Step 3: Medium Summary
            msg = json.dumps({"agent": "medium", "message": "Consulting Google Gemma 3 for the séance prophecy..."})
            yield f"data: {msg}\n\n"
            haunting_data = "\n".join(
                f"- {r.file_path}: status={r.status.value}, ghost_score={r.ghost_score}, mortality_risk={r.mortality_risk}"
                for r in reports[:20]
            )
            from services.github_client import GitHubClient
            owner, repo_name = GitHubClient.parse_repo_url(repo_url)
            summary = await gemma.generate_summary(repo_name=repo_name, haunting_data=haunting_data)

            status_counts = {s: 0 for s in HauntingStatus}
            for r in reports:
                status_counts[r.status] += 1

            response_data = SeanceResponse(
                repo_name=repo_name,
                repo_url=repo_url,
                total_files_scanned=len(reports),
                dead_count=status_counts[HauntingStatus.DEAD],
                haunted_count=status_counts[HauntingStatus.HAUNTED],
                orphaned_count=status_counts[HauntingStatus.ORPHANED],
                cursed_count=status_counts[HauntingStatus.CURSED],
                alive_count=status_counts[HauntingStatus.ALIVE] + status_counts[HauntingStatus.FADING],
                haunting_reports=reports,
                summary=summary,
            )

            msg = json.dumps({"agent": "complete", "message": "The veil is parted. The séance is complete.", "result": response_data.model_dump()})
            yield f"data: {msg}\n\n"

        except Exception as e:
            sentry_sdk.capture_exception(e)
            msg = json.dumps({"agent": "error", "message": f"The séance was disrupted: {str(e)}"})
            yield f"data: {msg}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
