"""Knows which calendar providers exist and which are configured."""
from __future__ import annotations

from integrations.google_calendar import GoogleCalendar
from integrations.microsoft_calendar import MicrosoftCalendar

PROVIDERS = {p.name: p for p in (GoogleCalendar(), MicrosoftCalendar())}


def get(name: str):
    return PROVIDERS.get(name)


def all_providers():
    return list(PROVIDERS.values())


def configured():
    return [p for p in PROVIDERS.values() if p.is_configured()]
