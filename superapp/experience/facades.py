"""Stable facades over the experience modules (API compatibility).

Thin wrappers so surfaces import one place. No logic here.
"""

from __future__ import annotations

from typing import Any

from superapp.experience import briefing as _briefing
from superapp.experience import insights as _insights
from superapp.experience import keepsake as _keepsake


def briefing() -> dict[str, Any]:
    """Today at the door: greeting + true line + suggestion + witness."""
    return _briefing.briefing()


def alive() -> dict[str, Any]:
    """What's breathing today: live habits, moving goals, movement."""
    return _briefing.alive()


def climate(lens: str = "start") -> dict[str, Any]:
    """Ranked insight cards (Rest/Body/Mind/Momentum) for a lens."""
    return _insights.climate(lens)


def mirror() -> dict[str, Any]:
    """The week's weave, threads, trends, reflection + question."""
    return _insights.mirror()


def keepsake() -> dict[str, Any]:
    """You room: letter, recognitions, kept moments, self-knowledge."""
    return _keepsake.keepsake()


def moments() -> dict[str, Any]:
    """Warm one-liners earned from real data + next invitation."""
    return _keepsake.moments()


def whisper_line(dimension: str = "today") -> dict[str, Any]:
    """Ambient companion: one specific line for a dimension."""
    from superapp.experience import whisper as _whisper

    return _whisper.whisper(dimension)
