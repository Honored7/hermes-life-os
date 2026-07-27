"""Wellness endpoints — the eyes, the ingest door, and the bounded companion."""
import json
from typing import List, Optional

from fastapi import APIRouter
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
