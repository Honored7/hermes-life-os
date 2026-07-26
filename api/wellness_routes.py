"""Wellness endpoints — the companion's eyes (sleep rhythm, and more to come)."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/insights/rhythm")
async def insights_rhythm():
    from wellness.vitals import rhythm_payload
    return rhythm_payload()
