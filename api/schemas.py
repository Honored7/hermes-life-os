"""
Pydantic models for API request/response validation.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ─── Requests ─────────────────────────────────────────────────────────

class MoodLogRequest(BaseModel):
    """User logs an emotional state."""
    state: str = Field(..., description="Emotional state: angry, anxious, stressed, sad, lonely, overwhelmed, restless, low_energy, frustrated, good")
    severity: int = Field(5, ge=1, le=10, description="Intensity 1-10")
    message: str = Field("", description="Optional: what the user says")
    context: dict = Field(default_factory=dict, description="Location, time_available_min, etc.")


class InterventionCompleteRequest(BaseModel):
    """User finished an intervention."""
    intervention_id: int
    state: str
    severity_before: int = Field(..., ge=1, le=10)
    severity_after: Optional[int] = Field(None, ge=1, le=10)
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: str = ""


class WinCelebrationRequest(BaseModel):
    """User shares a win."""
    description: str = Field(..., min_length=1)


class PreparationRequest(BaseModel):
    """User wants to prepare for an upcoming stressor."""
    stressor: str = Field(..., min_length=1)


class DreamLogRequest(BaseModel):
    """User logs a dream."""
    description: str
    tone: str = Field("neutral", description="positive, negative, neutral, nightmare")


class ProtocolAdvanceRequest(BaseModel):
    """Advance to the next step in a protocol."""
    protocol_id: str
    current_step: int
    feedback: Optional[str] = None


# ─── Responses ────────────────────────────────────────────────────────

class InterventionResponse(BaseModel):
    id: int
    name: str
    family: str
    duration_seconds: int
    format: str
    steps: list[str]
    wizard_intro: str = ""
    wizard_outro: str = ""


class RecommendationItem(BaseModel):
    id: int
    name: str
    reason: str


class ProtocolStepResponse(BaseModel):
    step_number: int
    intervention_id: Optional[int]
    intervention_name: str
    wizard_message: str
    is_check_in: bool


class ProtocolResponse(BaseModel):
    id: str
    name: str
    total_steps: int
    current_step: int
    steps: list[ProtocolStepResponse]


class WizardResponse(BaseModel):
    """The wizard's full response to a mood log."""
    wizard_message: str
    intervention: Optional[InterventionResponse] = None
    protocol: Optional[ProtocolResponse] = None
    session_config: Optional[dict] = None
    alternatives: list[RecommendationItem] = []


class SessionConfig(BaseModel):
    intervention_id: int
    name: str
    format: str
    duration_seconds: int
    steps: list[str]
    breathing_pattern: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    interventions_loaded: int
    protocols_loaded: int
