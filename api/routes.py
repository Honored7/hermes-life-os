"""
Wellness API routes — uses demo/wellness/ modules.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.responses import StreamingResponse
import json as json_mod

from wellness.interventions import INTERVENTIONS, get_intervention, get_by_state, get_all
from wellness.protocols import PROTOCOLS, get_all_protocols
from wellness.wizard import Wizard
from api.schemas import (
    MoodLogRequest, InterventionCompleteRequest, WinCelebrationRequest,
    PreparationRequest, DreamLogRequest, ProtocolAdvanceRequest,
    WizardResponse, InterventionResponse, RecommendationItem,
    ProtocolResponse, ProtocolStepResponse, HealthResponse,
)

router = APIRouter()

_wizard = Wizard()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: dict = Field(default_factory=dict)

class LLMConfigRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None


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
    return _wizard.status()

@router.post("/llm/configure")
async def llm_configure(req: LLMConfigRequest):
    global _wizard
    _wizard = Wizard(provider=req.provider, model=req.model)
    return {"message": "Reconfigured", "status": _wizard.status()}


# ─── Interventions ────────────────────────────────────────────────────

@router.get("/interventions")
async def list_interventions():
    return [
        InterventionResponse(
            id=iv.id, name=iv.name, family=iv.family.value,
            duration_seconds=iv.duration_seconds, format=iv.format.value,
            steps=list(iv.steps), wizard_intro=iv.wizard_intro, wizard_outro=iv.wizard_outro,
        ) for iv in get_all()
    ]

@router.get("/interventions/{intervention_id}")
async def get_single(intervention_id: int):
    iv = get_intervention(intervention_id)
    if not iv:
        raise HTTPException(404, f"Intervention {intervention_id} not found")
    return InterventionResponse(
        id=iv.id, name=iv.name, family=iv.family.value,
        duration_seconds=iv.duration_seconds, format=iv.format.value,
        steps=list(iv.steps), wizard_intro=iv.wizard_intro, wizard_outro=iv.wizard_outro,
    )

@router.get("/interventions/by-state/{state}")
async def by_state(state: str):
    results = get_by_state(state)
    if not results:
        raise HTTPException(404, f"No interventions for '{state}'")
    return [
        InterventionResponse(
            id=iv.id, name=iv.name, family=iv.family.value,
            duration_seconds=iv.duration_seconds, format=iv.format.value, steps=list(iv.steps),
        ) for iv in results
    ]


# ─── Wizard ───────────────────────────────────────────────────────────

@router.post("/wizard/respond", response_model=WizardResponse)
async def wizard_respond(req: MoodLogRequest):
    result = _wizard.respond_to_state(
        state=req.state, severity=req.severity,
        user_message=req.message, context=req.context,
    )
    return _build_response(result)

@router.post("/wizard/chat")
async def wizard_chat(req: ChatRequest):
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

@router.post("/wizard/chat/stream")
async def wizard_chat_stream(req: ChatRequest):
    """Stream the wizard's response token by token (SSE)."""
    def generate():
        for chunk in _wizard.chat_stream(req.message, req.context):
            yield f"data: {json_mod.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# ─── Protocols ────────────────────────────────────────────────────────

@router.get("/protocols")
async def list_protocols():
    return [
        {
            "id": p.id, "name": p.name, "description": p.description,
            "trigger_state": p.trigger_state, "trigger_severity_min": p.trigger_severity_min,
            "total_steps": len(p.steps), "total_duration_seconds": p.total_duration_seconds,
        } for p in get_all_protocols()
    ]

@router.post("/protocol/advance")
async def protocol_advance(req: ProtocolAdvanceRequest):
    result = _wizard.advance_protocol(req.protocol_id, req.current_step, req.feedback)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


# ─── Helpers ──────────────────────────────────────────────────────────

def _build_response(result: dict) -> WizardResponse:
    intervention = None
    if result.get("intervention"):
        iv = result["intervention"]
        intervention = InterventionResponse(
            id=iv["id"], name=iv["name"], family=iv["family"],
            duration_seconds=iv["duration_seconds"], format=iv["format"],
            steps=iv["steps"],
            wizard_intro=iv.get("wizard_intro", ""), wizard_outro=iv.get("wizard_outro", ""),
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
                ) for s in p["steps"]
            ],
        )

    return WizardResponse(
        wizard_message=result["wizard_message"],
        intervention=intervention, protocol=protocol,
        session_config=result.get("session_config"),
        alternatives=[
            RecommendationItem(id=a["id"], name=a["name"], reason=a["reason"])
            for a in result.get("alternatives", [])
        ],
    )
