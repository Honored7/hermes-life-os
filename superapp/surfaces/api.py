"""Motif HTTP skin — FastAPI over the super-app seams + PWA host.

Every route delegates to exactly one facade (experience / writes /
relief / intelligence). No business logic, no demo/* imports, no storage
access here. Serves the built PWA (anima-app/dist) same-origin so the
reference client works with zero config:

    HOME=/tmp/demohome .venv/bin/python -m superapp.surfaces.api
    # open http://127.0.0.1:8000

LLM-free by design: wizard/companion answers are composed from the
relief library's own voice lines + personal ranking (no provider key).
The full LLM wizard migrates later behind the same routes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import (
        FileResponse,
        JSONResponse,
        StreamingResponse,
    )
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - import error surfaces at launch
    raise SystemExit("FastAPI is required: pip install fastapi uvicorn")

from superapp.surfaces import keepers, rhythm, writes

app = FastAPI(title="Motif — Life Companion", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ───────────────────────────────────────────────────────────

def _iv_to_dict(iv) -> dict[str, Any]:
    return {
        "id": iv.id,
        "name": iv.name,
        "family": iv.family.value,
        "description": iv.description,
        "states": [s.value for s in iv.states],
        "severity_range": list(iv.severity_range),
        "duration_seconds": iv.duration_seconds,
        "format": iv.format.value,
        "intensity": iv.intensity.value,
        "requires": list(iv.requires),
        "steps": list(iv.steps),
        "wizard_intro": iv.wizard_intro,
        "wizard_outro": iv.wizard_outro,
        "contraindications": list(iv.contraindications),
        "tags": list(iv.tags),
    }


def _sse_tokens(text: str):
    words = text.split()
    chunk, n = [], 4
    for i in range(0, len(words), n):
        chunk = words[i:i + n]
        yield f"data: {json.dumps({'type': 'token', 'text': ' '.join(chunk) + ' '})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def _compose_relief_text(state: str, severity: int,
                         context: dict | None = None) -> dict[str, Any]:
    """Deterministic wizard answer: safety gate, then ranked library."""
    from superapp.relief import safety
    from superapp.relief import recommend as relief_recommend

    message = (context or {}).get("message", "")
    if message and safety.gate(message) is not None:
        return {"wizard_message": safety.safety_response(),
                "recommendations": [], "protocol": None, "crisis": True}
    result = relief_recommend(state=state, severity=severity,
                              context=context or {})
    if not result.recommendations:
        return {"wizard_message": (
            "I'm here with you. Name what you're feeling — even roughly — "
            "and we'll find one small thing that helps." if not message
            else "Thank you for telling me. I'm still learning what helps "
            "you most; for now, one slow breath with me?"),
            "recommendations": [], "protocol": result.protocol,
            "crisis": False}
    top = result.recommendations[0]
    from superapp.relief.interventions import INTERVENTIONS

    iv = next((v for v in INTERVENTIONS.values() if v.name == top.name),
              None)
    if iv is not None:
        text = f"{iv.wizard_intro} {iv.wizard_outro}".strip()
    else:
        text = f"Want to try {top.name}? {top.reason}."
    if result.protocol:
        text += f" If it feels right, we can walk the {result.protocol} together, one step at a time."
    return {"wizard_message": text,
            "recommendations": [r.name for r in result.recommendations],
            "protocol": result.protocol, "crisis": False}


# ── meta ──────────────────────────────────────────────────────────────

@app.get("/api/v1/info")
async def info():
    from superapp.relief.interventions import INTERVENTIONS
    from superapp.relief.protocols import PROTOCOLS

    return {"name": "Motif", "version": "1.0.0",
            "interventions": len(INTERVENTIONS),
            "protocols": len(PROTOCOLS)}


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


# ── today ─────────────────────────────────────────────────────────────

@app.get("/api/v1/today/briefing")
async def today_briefing():
    from superapp.experience import briefing

    return briefing()


@app.get("/api/v1/today/alive")
async def today_alive():
    from superapp.experience import alive

    return alive()


# ── life ──────────────────────────────────────────────────────────────

@app.get("/api/v1/life/stats")
async def life_stats():
    from superapp.experience import dimension_stats

    return dimension_stats()


@app.get("/api/v1/life/today")
async def life_today():
    from superapp.experience import life

    return life.get_today_summary()


@app.get("/api/v1/life/dims")
async def life_dims():
    from superapp.experience import store

    def last8(load_fn):
        try:
            items = load_fn() or []
        except Exception:
            items = []
        return items[-8:]

    habits = last8(store.load_habits)
    goals = [g for g in last8(store.load_goals) if (g.get("name") or "").strip()]
    active_goals = [g for g in goals if float(g.get("progress") or 0) < 100]
    return {
        "goals": {
            "items": goals,
            "active": len(active_goals),
            "avg": round(sum(float(g.get("progress") or 0)
                             for g in active_goals) / len(active_goals))
            if active_goals else 0,
            "templates": [],
        },
        "habits": {
            "items": habits[-8:],
            "active": len([h for h in habits
                           if float(h.get("streak") or 0) > 0]),
        },
        "nutrition": {"items": last8(store.load_nutrition)},
        "fitness": {"items": last8(store.load_fitness)},
        "focus": {"items": last8(store.load_focus)},
        "mental": {"items": last8(store.load_mental)},
    }


@app.get("/api/v1/life/dimensions")
async def life_dimensions():
    return await life_dims()


@app.get("/api/v1/life/sleep")
async def life_sleep():
    from superapp.experience import rhythm_payload

    return rhythm_payload()


@app.get("/api/v1/life/hydration")
async def life_hydration():
    from superapp.experience import dimension_stats

    return dimension_stats()["hydration"]


@app.get("/api/v1/life/nutrition")
async def life_nutrition():
    from superapp.experience import dimension_stats

    return dimension_stats()["nutrition"]


@app.get("/api/v1/life/fitness")
async def life_fitness():
    from superapp.experience import dimension_stats

    return dimension_stats()["fitness"]


@app.get("/api/v1/life/focus")
async def life_focus():
    from superapp.experience import dimension_stats

    return dimension_stats()["focus"]


@app.get("/api/v1/life/mental")
async def life_mental():
    from superapp.experience import dimension_stats

    return dimension_stats()["mental"]


@app.get("/api/v1/life/journal")
async def journal_list():
    from superapp.experience import list_entries

    return {"entries": list_entries()}


class JournalReq(BaseModel):
    html: str = ""
    text: str = ""
    is_dream: bool = False


@app.post("/api/v1/life/journal")
async def journal_add(req: JournalReq):
    from superapp.experience import add_entry

    return {"entry": add_entry(req.html, req.text, req.is_dream)}


@app.delete("/api/v1/life/journal/{entry_id}")
async def journal_delete(entry_id: str):
    from superapp.experience import delete_entry

    return {"deleted": delete_entry(entry_id)}


@app.post("/api/v1/life/log-dim")
async def life_log_dim(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")
    kind = payload.get("kind", "")
    try:
        return writes.write(kind, payload)
    except writes.UnknownKindError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except writes.WriteValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


class LifeLogRequest(BaseModel):
    dimension: str = ""
    note: str = ""
    glasses: Optional[int] = None
    hours: Optional[float] = None
    quality: Optional[int] = None


@app.post("/api/v1/life/log")
async def life_log(req: LifeLogRequest):
    if req.dimension == "hydration":
        return writes.log_water(req.glasses or 1)
    if req.dimension == "sleep":
        return writes.log_sleep(req.hours or 0, req.quality or 5)
    return writes.log_note(req.note or req.dimension, req.dimension or "note")


# ── insights ──────────────────────────────────────────────────────────

@app.get("/api/v1/insights/mirror")
async def insights_mirror():
    from superapp.experience import mirror

    return mirror()


@app.get("/api/v1/insights/climate")
async def insights_climate(lens: str = "start"):
    from superapp.experience import climate

    return climate(lens if lens in ("start", "30") else "start")


@app.get("/api/v1/insights/mood-weather")
async def insights_mood_weather():
    from superapp.experience import mood_weather

    return mood_weather()


@app.get("/api/v1/insights/mood-trend")
async def insights_mood_trend():
    from superapp.experience import mood_trend

    return mood_trend()


@app.get("/api/v1/insights/rhythm")
async def insights_rhythm():
    from superapp.experience import rhythm_payload

    return rhythm_payload()


@app.get("/api/v1/insights")
async def insights_summary():
    from superapp.experience import get_insights_summary

    return get_insights_summary()


# ── you ───────────────────────────────────────────────────────────────

@app.get("/api/v1/you/keepsake")
async def you_keepsake():
    from superapp.experience import keepsake

    return keepsake()


@app.get("/api/v1/you/moments")
async def you_moments():
    from superapp.experience import moments

    return moments()


@app.get("/api/v1/you/export")
async def you_export():
    return keepers.export_all()


@app.post("/api/v1/you/wipe")
async def you_wipe():
    return keepers.wipe_all()


# ── relief library + wizard (deterministic, LLM-free) ─────────────────

@app.get("/api/v1/interventions")
async def list_interventions():
    from superapp.relief.interventions import INTERVENTIONS

    return [_iv_to_dict(iv) for iv in INTERVENTIONS.values()]


@app.get("/api/v1/interventions/by-state/{state}")
async def interventions_by_state(state: str):
    from superapp.relief.interventions import get_by_state

    return [_iv_to_dict(iv) for iv in get_by_state(state)]


@app.get("/api/v1/interventions/{intervention_id}")
async def get_intervention(intervention_id: int):
    from superapp.relief.interventions import get_intervention as _get

    iv = _get(intervention_id)
    if iv is None:
        raise HTTPException(status_code=404, detail="Not found")
    return _iv_to_dict(iv)


class WizardRespondReq(BaseModel):
    state: str = "stressed"
    severity: int = 5
    message: str = ""
    context: dict[str, Any] | None = None


@app.post("/api/v1/wizard/respond")
async def wizard_respond(req: WizardRespondReq):
    ctx = dict(req.context or {})
    if req.message:
        ctx["message"] = req.message
    return _compose_relief_text(req.state, req.severity, ctx)


@app.post("/api/v1/wizard/respond/stream")
async def wizard_respond_stream(req: WizardRespondReq):
    ctx = dict(req.context or {})
    if req.message:
        ctx["message"] = req.message
    text = _compose_relief_text(req.state, req.severity, ctx)["wizard_message"]
    return StreamingResponse(_sse_tokens(text),
                             media_type="text/event-stream")


@app.post("/api/v1/wizard/narrate/stream")
async def wizard_narrate_stream(req: WizardRespondReq):
    return await wizard_respond_stream(req)


class ChatReq(BaseModel):
    message: str = ""
    state: str = "stressed"
    severity: int = 5


@app.post("/api/v1/wizard/chat")
async def wizard_chat(req: ChatReq):
    return _compose_relief_text(req.state, req.severity,
                                {"message": req.message})


@app.post("/api/v1/companion/chat/stream")
async def companion_chat_stream(req: ChatReq):
    text = _compose_relief_text(req.state, req.severity,
                                {"message": req.message})["wizard_message"]
    return StreamingResponse(_sse_tokens(text),
                             media_type="text/event-stream")


class CompleteReq(BaseModel):
    name: str = ""
    intervention_id: int = 0
    state: str = ""
    severity_before: int = 5
    severity_after: Optional[int] = None
    effectiveness: Optional[int] = None
    effectiveness_rating: Optional[int] = None


@app.post("/api/v1/wizard/complete")
async def wizard_complete(req: CompleteReq):
    name = req.name
    if not name and req.intervention_id:
        from superapp.relief.interventions import (
            get_intervention as _get,
        )

        iv = _get(req.intervention_id)
        name = iv.name if iv else ""
    eff = req.effectiveness if req.effectiveness is not None \
        else req.effectiveness_rating
    return writes.log_relief_outcome(
        name, req.state or "stressed", severity_before=req.severity_before,
        severity_after=req.severity_after, effectiveness=eff)


class CelebrateReq(BaseModel):
    description: str = ""
    win: str = ""


@app.post("/api/v1/wizard/celebrate")
async def wizard_celebrate(req: CelebrateReq):
    text = req.description or req.win or "a good moment"
    writes.log_note(text, "win")
    return {"wizard_message": (
        f"That's real — {text}. Let's keep it somewhere safe for the "
        "harder days. What made it possible?")}


# ── ingest + integrations (graceful) ──────────────────────────────────

@app.post("/api/v1/ingest/health")
async def ingest_health(request: Request):
    from superapp.experience import ingest

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")
    return {"ingested": ingest.ingest(payload)}


@app.get("/api/v1/integrations/calendar")
async def calendar_status():
    from superapp.experience.store import load_calendar_tokens

    tokens = load_calendar_tokens()
    return {"connected": bool(tokens),
            "providers": [k for k, v in tokens.items() if v]}


@app.get("/api/v1/integrations/calendar/events")
async def calendar_events(limit: int = 5):
    return {"events": [], "note": "No calendar connected yet."}


@app.post("/api/v1/integrations/calendar/{provider}/disconnect")
async def calendar_disconnect(provider: str):
    return {"provider": provider, "connected": False}


@app.get("/api/v1/integrations/calendar/{provider}/start")
async def calendar_start(provider: str):
    return {"provider": provider, "connected": False,
            "note": "OAuth migrates with the integrations layer."}


# ── rhythm (scheduler over HTTP, for the PWA/debug) ───────────────────

@app.get("/api/v1/rhythm/{mode}")
async def rhythm_preview(mode: str):
    render = {"morning": rhythm.render_morning,
              "checkin": rhythm.render_checkin,
              "evening": rhythm.render_evening,
              "weekly": rhythm.render_weekly}.get(mode)
    if render is None:
        raise HTTPException(status_code=404, detail="Unknown mode")
    return {"mode": mode, "text": render()}


# ── PWA host (same origin, SPA fallback) ──────────────────────────────

DIST = Path(__file__).resolve().parent.parent.parent / "anima-app" / "dist"


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    if DIST.is_dir():
        candidate = DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = DIST / "index.html"
        if index.is_file():
            return FileResponse(index)
    return JSONResponse({
        "name": "Motif API",
        "note": "PWA not built. API is live under /api/v1.",
        "docs": "/docs",
    })


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(
        os.environ.get("MOTIF_PORT", "8000")))


if __name__ == "__main__":
    main()
