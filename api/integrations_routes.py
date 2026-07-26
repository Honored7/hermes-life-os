"""Calendar integration endpoints — OAuth dance, status, events."""
from __future__ import annotations

import urllib.parse

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from integrations import registry, sync
from integrations.calendar_base import (
    CalendarError, Disconnected, NotConfigured, clear_token, get_token, set_token,
)
from integrations.nonces import consume, create

router = APIRouter()

_APP_ROOT = "http://localhost:5173"  # dev UI; overridden by ?redirect= on /start


def _status_one(prov) -> dict:
    token = get_token(prov.name)
    return {
        "name": prov.name,
        "configured": prov.is_configured(),
        "connected": bool(token),
        "account": (token or {}).get("account_label", ""),
    }


@router.get("/calendar")
async def calendar_status():
    return {"providers": [_status_one(p) for p in registry.all_providers()]}


@router.get("/calendar/{provider}/start")
async def calendar_start(provider: str, redirect: str = _APP_ROOT):
    prov = registry.get(provider)
    if not prov:
        raise HTTPException(404, f"Unknown provider '{provider}'")
    if not prov.is_configured():
        raise HTTPException(503, f"'{provider}' is not configured on this server")
    nonce = create(redirect)
    return RedirectResponse(prov.auth_url(nonce))


@router.get("/calendar/{provider}/callback")
async def calendar_callback(provider: str, code: str = "", state: str = "", error: str = ""):
    prov = registry.get(provider)
    redirect = consume(state) or _APP_ROOT
    sep = "&" if "?" in redirect else "?"

    if error or not prov:
        msg = error or "unknown provider"
        return RedirectResponse(f"{redirect}{sep}error={urllib.parse.quote(msg)}")

    try:
        token = prov.exchange_code(code)
        token["account_label"] = prov.account_label(token)
        import time
        token["connected_at"] = time.time()
        set_token(prov.name, token)
    except NotConfigured:
        return RedirectResponse(f"{redirect}{sep}error=not_configured")
    except CalendarError as e:
        return RedirectResponse(f"{redirect}{sep}error={urllib.parse.quote(str(e)[:120])}")

    return RedirectResponse(f"{redirect}{sep}connected={provider}")


@router.post("/calendar/{provider}/disconnect")
async def calendar_disconnect(provider: str):
    prov = registry.get(provider)
    if not prov:
        raise HTTPException(404, f"Unknown provider '{provider}'")
    clear_token(prov.name)
    return {"disconnected": provider}


@router.get("/calendar/events")
async def calendar_events(limit: int = 5, force: bool = False):
    events, meta = sync.get_upcoming(limit=limit, force=force)
    return {
        "events": [e.to_dict() for e in events],
        "meta": meta,
    }
