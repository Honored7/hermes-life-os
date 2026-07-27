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
