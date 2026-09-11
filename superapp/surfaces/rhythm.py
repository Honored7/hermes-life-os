"""Daily rhythm: the scheduler's runner + notifier for the super-app.

Upstream demo/scheduler.py is intentionally left unforked: its
default_schedule() (07:00 morning, 12:00 checkin, 18:00 evening, Monday
08:00 weekly, 20:00 nudge_check, 20:30 backup) already names the modes,
and run_scheduler() takes injected callables. This module IS those
callables:

- make_runner() builds runner(mode) -> str. Super-app modes
  (morning/checkin/evening/weekly) render deterministically from the
  experience layer — no LLM, no provider key, works on a plane.
  Operational modes (nudge_check/backup) delegate to the upstream
  implementations. Unknown modes return "" (silent skip).
- make_notifier() builds notifier(title, content) -> None on top of
  upstream send_notification (console default; webhook/telegram/email
  via HERMES_NOTIFY_CHANNEL; never raises).
- run_rhythm() wires schedule + runner + notifier into upstream
  run_scheduler(). Pass clock/sleeper/max_iterations in tests.

A runner exception never pages anyone: it is caught and yields ""
so the scheduler stays silent instead of notifying a traceback.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


def _demo():
    demo = str(Path(__file__).resolve().parent.parent.parent / "demo")
    if demo not in sys.path:
        sys.path.insert(0, demo)
    import scheduler as upstream_scheduler

    return upstream_scheduler


def daily_rhythm():
    """The upstream default schedule (unforked, single source of truth)."""
    return _demo().default_schedule()


# ── renderers: experience dicts -> plain-text briefings ───────────────

def render_morning() -> str:
    from superapp.experience import alive, briefing

    b = briefing()
    lines = [b["greeting"] + ".", b["true_line"]]
    a = alive()
    if a["habits"]:
        lines.append("Alive today: " + ", ".join(a["habits"]) + ".")
    if a["goals"]:
        lines.append("Moving: " + ", ".join(
            f"{g['name']} ({g['progress']}%)" for g in a["goals"]) + ".")
    s = (b.get("suggestion") or {})
    if s.get("text"):
        lines.append("One gentle suggestion: " + s["text"])
    return "\n".join(lines)


def render_checkin() -> str:
    from superapp.experience import alive, briefing

    b = briefing()
    s = (b.get("suggestion") or {})
    lines = ["Midday check-in."]
    if s.get("text"):
        lines.append("A nudge, only if you want it: " + s["text"])
    a = alive()
    if a["habits"]:
        lines.append("Still alive: " + ", ".join(a["habits"]) + ".")
    if a["move_min"]:
        lines.append(f"Movement so far: {a['move_min']} min.")
    return "\n".join(lines)


def render_evening() -> str:
    from superapp.experience import briefing, keepsake

    b = briefing()
    lines = ["The day is closing.", b["true_line"]]
    try:
        recs = (keepsake().get("recognitions") or [])[:2]
    except Exception:
        recs = []
    for r in recs:
        lines.append("Kept today: " + r)
    lines.append("Name one win before sleep — even a small one counts.")
    return "\n".join(lines)


def render_weekly(lens: str = "start") -> str:
    from superapp.experience import climate

    c = climate(lens)
    lines = [c.get("headline", "Weekly review.")]
    for card in (c.get("cards") or [])[:4]:
        lines.append(f"{card['title']}: {card['finding']}")
        if card.get("proof"):
            lines.append(f"  Proof: {card['proof']}")
        if card.get("action"):
            action = card["action"]
            label = action.get("label", "one small step") \
                if isinstance(action, dict) else str(action)
            lines.append(f"  Try: {label}")
    signals = (c.get("signals") or {}).get("correlations") or []
    if signals:
        top = signals[0]
        lines.append(
            f"Engine room corroborates: {top['metric_a']} x "
            f"{top['metric_b']} (r={top['r']}, {top['n_days']} days).")
    return "\n".join(lines)


_RENDERERS: dict[str, Callable[[], str]] = {
    "morning": render_morning,
    "checkin": render_checkin,
    "evening": render_evening,
    "weekly": render_weekly,
}


# ── runner + notifier (the injected callables) ───────────────────────

def make_runner() -> Callable[[str], str]:
    """runner(mode) -> str. Empty string means 'nothing to send'."""

    def runner(mode: str) -> str:
        render = _RENDERERS.get(mode)
        if render is not None:
            try:
                return render()
            except Exception:
                return ""
        return _upstream_mode(mode)

    return runner


def _upstream_mode(mode: str) -> str:
    """Operational modes stay upstream-owned (no reimplementation)."""
    try:
        demo = str(Path(__file__).resolve().parent.parent.parent / "demo")
        if demo not in sys.path:
            sys.path.insert(0, demo)
        if mode == "nudge_check":
            from nudges import generate_nudges

            nudges = generate_nudges()
            return "\n".join(nudges) if nudges else ""
        if mode == "backup":
            from backup import run_backup

            try:
                out_path = run_backup()
                return "" if out_path else "Backup failed: no path returned."
            except Exception as exc:
                return f"Backup failed: {exc}"
    except Exception:
        return ""
    return ""


def make_notifier(channel: str | None = None) -> Callable[[str, str], Any]:
    """notifier(title, content). Delivery failures never raise (upstream
    contract); the result is returned for logging/tests."""

    def notifier(title: str, content: str) -> Any:
        demo = str(Path(__file__).resolve().parent.parent.parent / "demo")
        if demo not in sys.path:
            sys.path.insert(0, demo)
        from notifications import send_notification

        return send_notification(title, content, channel=channel)

    return notifier


def run_rhythm(poll_seconds: int = 60,
               max_iterations: int | None = None,
               clock: Callable | None = None,
               sleeper: Callable | None = None,
               channel: str | None = None) -> dict:
    """Run the daily rhythm loop. Blocking unless max_iterations is set
    (tests, dry runs). Returns the scheduler's last_run map."""
    sched = _demo()
    return sched.run_scheduler(
        daily_rhythm(), runner=make_runner(),
        notifier=make_notifier(channel), poll_seconds=poll_seconds,
        max_iterations=max_iterations, clock=clock, sleeper=sleeper)
