"""Wellness endpoints — the companion's eyes, and the door its sensors walk through."""
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


@router.get("/insights/rhythm")
async def insights_rhythm():
    from wellness.vitals import rhythm_payload
    return rhythm_payload()


class HealthPayload(BaseModel):
    source: str = "wearable"
    sleep: Optional[List[dict]] = None
    heart_rate: Optional[List[dict]] = None
    steps: Optional[List[dict]] = None


@router.post("/ingest/health")
async def ingest_health(payload: HealthPayload):
    from wellness.ingest import ingest
    return {"ingested": ingest(payload.model_dump(exclude_none=True))}


@router.get("/insights/mood-weather")
async def insights_mood_weather():
    from wellness.insights import mood_weather
    return mood_weather()
