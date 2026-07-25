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


# ─── Streaming check-in (intervention appears instantly, voice streams) ──
@router.post("/wizard/respond/stream")
async def wizard_respond_stream(req: MoodLogRequest):
    """Check in with a mood. Returns the intervention/session data immediately,
    then streams the wizard's spoken response token by token."""
    from wellness.streaming import respond_stream

    def generate():
        for event in respond_stream(
            _wizard, req.state, req.severity, req.message, req.context,
        ):
            yield f"data: {json_mod.dumps(event)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ─── Fresh per-step journey narration ────────────────────────────────
class NarrateRequest(BaseModel):
    protocol_id: str
    step_number: int
    state: str
    severity: int = 5
    message: str = ""


@router.post("/wizard/narrate/stream")
async def wizard_narrate_stream(req: NarrateRequest):
    """Stream a freshly-spoken narration for one step of a protocol journey."""
    from wellness.streaming import narrate_step_stream

    def generate():
        for event in narrate_step_stream(
            _wizard, req.protocol_id, req.step_number, req.state, req.severity, req.message,
        ):
            yield f"data: {json_mod.dumps(event)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ─── Life — the nine dimensions ──────────────────────────────────────
class LifeLogRequest(BaseModel):
    dimension: str
    glasses: Optional[int] = None
    hours: Optional[float] = None
    quality: Optional[int] = None
    note: str = ""


@router.get("/life/today")
async def life_today():
    """Today's picture across the dimensions."""
    from wellness.life import get_today_summary
    return get_today_summary()


@router.post("/life/log")
async def life_log(req: LifeLogRequest):
    """Log something toward a dimension."""
    from wellness.life import add_water, log_sleep, log_generic
    if req.dimension == "hydration":
        return add_water(req.glasses or 1)
    if req.dimension == "sleep":
        return log_sleep(req.hours or 0, req.quality or 5)
    return log_generic(req.dimension, req.note)


# ─── Insights — the wizard reflects ──────────────────────────────────
@router.get("/insights")
async def insights():
    from wellness.insights import get_insights_summary
    return get_insights_summary()


@router.post("/insights/reflect/stream")
async def insights_reflect_stream():
    from wellness.insights import reflect_stream

    def generate():
        for event in reflect_stream(_wizard):
            yield f"data: {json_mod.dumps(event)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
