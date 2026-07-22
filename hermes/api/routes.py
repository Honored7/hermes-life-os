"""
API routes for the Hermes Wellness Wizard — v2 with LLM endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from hermes.wellness.interventions import INTERVENTIONS, get_intervention, get_by_state, get_all
from hermes.wellness.protocols import PROTOCOLS, get_all_protocols
from hermes.wellness.engine import WellnessEngine
from hermes.wizard import Wizard
from hermes.api.schemas import (
    MoodLogRequest,
    InterventionCompleteRequest,
    WinCelebrationRequest,
    PreparationRequest,
    DreamLogRequest,
    ProtocolAdvanceRequest,
    WizardResponse,
    InterventionResponse,
    RecommendationItem,
    ProtocolResponse,
    ProtocolStepResponse,
    HealthResponse,
)
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# ─── Shared Wizard Instance ───────────────────────────────────────────
# Auto-detects LLM: Ollama → OpenAI → Anthropic → template fallback
_wizard = Wizard()
_engine = WellnessEngine()


# ─── Schemas for new endpoints ────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Say anything to the wizard")
    context: dict = Field(default_factory=dict)

class LLMConfigRequest(BaseModel):
    provider: str = Field("auto", description="auto, ollama, openai, anthropic, none")
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


# ─── Health & Status ──────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        interventions_loaded=len(INTERVENTIONS),
        protocols_loaded=len(PROTOCOLS),
    )

@router.get("/llm/status")
async def llm_status():
    """Check which LLM provider is active."""
    return _wizard.status()

@router.post("/llm/configure")
async def llm_configure(req: LLMConfigRequest):
    """Reconfigure the LLM provider at runtime."""
    global _wizard
    _wizard = Wizard(
        llm_provider=req.provider,
        llm_model=req.model,
        llm_api_key=req.api_key,
        llm_base_url=req.base_url,
    )
    return {"message": "LLM reconfigured", "status": _wizard.status()}


# ─── Interventions ────────────────────────────────────────────────────

@router.get("/interventions")
async def list_interventions():
    return [
        InterventionResponse(
            id=iv.id, name=iv.name, family=iv.family.value,
            duration_seconds=iv.duration_seconds, format=iv.format.value,
            steps=list(iv.steps), wizard_intro=iv.wizard_intro, wizard_outro=iv.wizard_outro,
        )
        for iv in get_all()
    ]

@router.get("/interventions/{intervention_id}")
async def get_single_intervention(intervention_id: int):
    iv = get_intervention(intervention_id)
    if not iv:
        raise HTTPException(status_code=404, detail=f"Intervention {intervention_id} not found")
    return InterventionResponse(
        id=iv.id, name=iv.name, family=iv.family.value,
        duration_seconds=iv.duration_seconds, format=iv.format.value,
        steps=list(iv.steps), wizard_intro=iv.wizard_intro, wizard_outro=iv.wizard_outro,
    )

@router.get("/interventions/by-state/{state}")
async def interventions_by_state(state: str):
    results = get_by_state(state)
    if not results:
        raise HTTPException(status_code=404, detail=f"No interventions for state '{state}'")
    return [
        InterventionResponse(
            id=iv.id, name=iv.name, family=iv.family.value,
            duration_seconds=iv.duration_seconds, format=iv.format.value, steps=list(iv.steps),
        )
        for iv in results
    ]


# ─── Wizard Core ──────────────────────────────────────────────────────

@router.post("/wizard/respond", response_model=WizardResponse)
async def wizard_respond(req: MoodLogRequest):
    result = _wizard.respond_to_state(
        state=req.state, severity=req.severity,
        user_message=req.message, context=req.context,
    )
    return _build_wizard_response(result)

@router.post("/wizard/chat")
async def wizard_chat(req: ChatRequest):
    """Free-form conversation with the wizard. Say anything."""
    return _wizard.chat(user_message=req.message, context=req.context)

@router.post("/wizard/complete")
async def wizard_complete(req: InterventionCompleteRequest):
    return _wizard.complete_intervention(
        intervention_id=req.intervention_id, state=req.state,
        severity_before=req.severity_before, severity_after=req.severity_after,
        effectiveness_rating=req.effectiveness_rating, notes=req.notes,
    )

@router.post("/wizard/celebrate")
async def wizard_celebrate(req: WinCelebrationRequest):
    return _wizard.celebrate_win(win_description=req.description)

@router.post("/wizard/prepare")
async def wizard_prepare(req: PreparationRequest):
    return _wizard.prepare_for_stressor(stressor_description=req.stressor)

@router.post("/wizard/dream")
async def wizard_dream(req: DreamLogRequest):
    return _wizard.respond_to_dream(dream_description=req.description, dream_tone=req.tone)


# ─── Protocols ────────────────────────────────────────────────────────

@router.get("/protocols")
async def list_protocols():
    return [
        {
            "id": p.id, "name": p.name, "description": p.description,
            "trigger_state": p.trigger_state, "trigger_severity_min": p.trigger_severity_min,
            "total_steps": len(p.steps), "total_duration_seconds": p.total_duration_seconds,
        }
        for p in get_all_protocols()
    ]

@router.post("/protocol/advance")
async def protocol_advance(req: ProtocolAdvanceRequest):
    result = _wizard.advance_protocol(
        protocol_id=req.protocol_id, current_step=req.current_step, user_feedback=req.feedback,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ─── Helpers ──────────────────────────────────────────────────────────

def _build_wizard_response(result: dict) -> WizardResponse:
    intervention = None
    if result.get("intervention"):
        iv = result["intervention"]
        intervention = InterventionResponse(
            id=iv["id"], name=iv["name"], family=iv["family"],
            duration_seconds=iv["duration_seconds"], format=iv["format"],
            steps=iv["steps"],
            wizard_intro=iv.get("wizard_intro", ""),
            wizard_outro=iv.get("wizard_outro", ""),
        )

    protocol = None
    if result.get("protocol"):
        p = result["protocol"]
        protocol = ProtocolResponse(
            id=p["id"], name=p["name"], total_steps=p["total_steps"], current_step=p["current_step"],
            steps=[
                ProtocolStepResponse(
                    step_number=s["step_number"], intervention_id=s["intervention_id"],
                    intervention_name=s["intervention_name"],
                    wizard_message=s["wizard_message"], is_check_in=s["is_check_in"],
                )
                for s in p["steps"]
            ],
        )

    alternatives = [
        RecommendationItem(id=a["id"], name=a["name"], reason=a["reason"])
        for a in result.get("alternatives", [])
    ]

    return WizardResponse(
        wizard_message=result["wizard_message"],
        intervention=intervention, protocol=protocol,
        session_config=result.get("session_config"), alternatives=alternatives,
    )
