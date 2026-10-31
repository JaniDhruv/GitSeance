"""
GitSeance Pydantic Models — Request/Response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class HauntingStatus(str, Enum):
    DEAD = "dead"           # 💀 Untouched 2+ years
    HAUNTED = "haunted"     # 👻 Has warning comments / sole author left
    ORPHANED = "orphaned"   # 🪦 Sole author inactive
    CURSED = "cursed"       # ☠️ Known CVEs or broken deps
    FADING = "fading"       # 🌫️ Declining activity
    ALIVE = "alive"         # ✨ Still active


# ──────────────────────────────────────────────
# Requests
# ──────────────────────────────────────────────

class SeanceRequest(BaseModel):
    """Request to begin a séance on a GitHub repository."""
    repo_url: str = Field(..., description="GitHub repository URL (e.g. https://github.com/owner/repo)")


class ChannelRequest(BaseModel):
    """Request to channel the ghost of a specific file."""
    repo_url: str
    file_path: str
    file_content: Optional[str] = None


class TTSRequest(BaseModel):
    """Request to speak a ghost's message via ElevenLabs."""
    text: str = Field(..., max_length=1000)
    voice: str = Field(default="aria", description="ElevenLabs voice ID or name")


class GhostChatMessage(BaseModel):
    """A single chat dialogue turn with a code ghost."""
    role: str = Field(..., description="'user' or 'ghost'")
    content: str


class GhostChatRequest(BaseModel):
    """Request to chat with a channeled developer ghost."""
    repo_url: str
    file_path: str
    author_name: str = "an ancient author"
    file_content: Optional[str] = None
    message: str = Field(..., max_length=1000)
    history: list[GhostChatMessage] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Response Components
# ──────────────────────────────────────────────

class FileMetrics(BaseModel):
    """Raw git metrics extracted for a single file."""
    file_path: str
    days_since_last_commit: int
    total_commits: int
    unique_authors: int
    bug_fix_commit_ratio: float
    lines_added: int
    lines_deleted: int
    has_tests: bool
    churn_velocity: float  # changes per month
    last_author: str
    last_commit_date: str
    last_commit_message: str


class HauntingReport(BaseModel):
    """Report for a single haunted file."""
    file_path: str
    status: HauntingStatus
    ghost_score: float = Field(..., ge=0.0, le=1.0, description="How 'haunted' this file is (0=alive, 1=dead)")
    mortality_risk: Optional[float] = Field(None, ge=0.0, le=1.0, description="TabPFN predicted mortality probability")
    metrics: FileMetrics
    warnings: list[str] = Field(default_factory=list)


class RevivalPatch(BaseModel):
    """A revival suggestion for dead code."""
    summary: str
    modern_replacement: Optional[str] = None
    migration_steps: list[str] = Field(default_factory=list)
    estimated_effort: str = "unknown"


class GhostChanneling(BaseModel):
    """The ghost's message from the Medium agent."""
    ghost_message: str          # Gemma's séance monologue (1st person)
    why_written: str            # Why the code was written this way
    last_wish: str              # What the ghost wishes was done differently
    revival_patch: RevivalPatch


class DependencyReplacement(BaseModel):
    """Modern replacement for a dead dependency from SerpApi."""
    old_package: str
    new_package: str
    reason: str
    url: str
    migration_difficulty: str = "unknown"
    cve_warnings: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Full Responses
# ──────────────────────────────────────────────

class SeanceResponse(BaseModel):
    """Full séance result for a repository."""
    repo_name: str
    repo_url: str
    total_files_scanned: int
    dead_count: int
    haunted_count: int
    orphaned_count: int
    cursed_count: int
    alive_count: int
    haunting_reports: list[HauntingReport]
    summary: str  # One-line séance summary


class ChannelResponse(BaseModel):
    """Response from channeling a specific file's ghost."""
    file_path: str
    channeling: GhostChanneling
    replacements: list[DependencyReplacement] = Field(default_factory=list)


class GhostChatResponse(BaseModel):
    """Response from conversing with a code ghost."""
    reply: str
    model_used: str = "gemma-4-26b-a4b-it"


class TTSResponse(BaseModel):
    """Response from ghost TTS."""
    audio_url: str  # base64 data URI or URL
    duration_seconds: Optional[float] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "alive"
    version: str
    ghosts_channeled: int = 0
