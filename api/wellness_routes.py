"""Wellness endpoints — the eyes, the ingest door, and the bounded companion."""
import json
from typing import List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


@router.get("/insights/rhythm")
async def insights_rhythm():
    from wellness.vitals import rhythm_payload
    return rhythm_payload()


@router.get("/insights/mood-weather")
async def insights_mood_weather():
    from wellness.insights import mood_weather
    return mood_weather()


class HealthPayload(BaseModel):
    source: str = "wearable"
    sleep: Optional[List[dict]] = None
    heart_rate: Optional[List[dict]] = None
    steps: Optional[List[dict]] = None


@router.post("/ingest/health")
async def ingest_health(payload: HealthPayload):
    from wellness.ingest import ingest
    return {"ingested": ingest(payload.model_dump(exclude_none=True))}


class CompanionReq(BaseModel):
    message: str


@router.post("/companion/chat/stream")
async def companion_chat_stream(req: CompanionReq):
    from api.routes import _wizard
    from wellness.companion import companion_chat_stream as _stream

    def generate():
        for ev in _stream(_wizard, req.message):
            yield f"data: {json.dumps(ev)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/life/dimensions")
async def life_dimensions():
    from wellness.dimensions import dimension_stats
    return dimension_stats()


class JournalReq(BaseModel):
    html: str = ""
    text: str = ""
    is_dream: bool = False


@router.get("/life/journal")
async def journal_list():
    from wellness.journal import list_entries
    return {"entries": list_entries()}


@router.post("/life/journal")
async def journal_add(req: JournalReq):
    from wellness.journal import add_entry
    return {"entry": add_entry(req.html, req.text, req.is_dream)}


@router.delete("/life/journal/{entry_id}")
async def journal_delete(entry_id: str):
    from wellness.journal import delete_entry
    return {"deleted": delete_entry(entry_id)}


@router.get("/insights/mood-trend")
async def insights_mood_trend():
    from wellness.insights import mood_trend
    return mood_trend()


@router.get("/you/moments")
async def you_moments():
    from wellness.you import moments
    return moments()


@router.get("/you/export")
async def you_export():
    from wellness.you import export_all
    return export_all()


@router.post("/you/wipe")
async def you_wipe():
    from wellness.you import wipe_all
    return wipe_all()


@router.get("/life/stats")
async def life_stats():
    from wellness.life_stats import dimension_stats
    return dimension_stats()


@router.post("/life/log-dim")
async def life_log(request: Request):
    from wellness import life_stats as LS, life
    payload = await request.json()
    kind = payload.get("kind")
    if kind == "water":
        return life.add_water(int(payload.get("glasses", 1)))
    if kind == "sleep":
        return life.log_sleep(float(payload.get("hours", 0)), int(payload.get("quality", 5)))
    if kind == "nutrition":
        return LS.log_nutrition(payload.get("food", ""), payload.get("calories", 0), payload.get("meal_time", ""))
    if kind == "fitness":
        return LS.log_fitness(payload.get("workout_type", ""), payload.get("duration_min", 0))
    if kind == "focus":
        return LS.log_focus(payload.get("task", ""), payload.get("duration_min", 25))
    if kind == "stress":
        return LS.log_stress(int(payload.get("score", 5)), payload.get("trigger", ""))
    if kind == "meditation":
        return LS.log_meditation(int(payload.get("duration_min", 10)))
    if kind == "gratitude":
        return LS.log_gratitude(payload.get("items", []))
    if kind == "habit":
        return LS.update_habit(payload.get("habit_name", ""), bool(payload.get("completed", True)))
    if kind == "goal":
        return LS.update_goal(payload.get("goal_name", ""), payload.get("progress"), payload.get("note", ""))
    return life.log_generic(kind or "note", payload.get("note", ""))
