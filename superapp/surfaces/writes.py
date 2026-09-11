"""Single write path. Every mutation in the super-app flows through here.

Surfaces (API routers, CLI, bots, scheduler workers) call these facades —
never demo/tools.dispatch_tool directly, never storage saves directly.
Each facade validates + coerces its inputs (raising WriteValidationError
instead of persisting garbage), dispatches exactly one upstream tool
(which owns the storage write AND the memory journal entry), and returns
a structured result the surface can render.

Unknown kinds raise UnknownKindError (never a silent no-op). Reads live
in superapp.experience; relief ranking in superapp.relief.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


class WriteValidationError(ValueError):
    """Caller input is missing or out of range — nothing was persisted."""


class UnknownKindError(KeyError):
    """No write op registered for this kind."""


def _tools():
    demo = str(Path(__file__).resolve().parent.parent.parent / "demo")
    if demo not in sys.path:
        sys.path.insert(0, demo)
    import tools as upstream_tools

    return upstream_tools


def _dispatch(name: str, payload: dict) -> str:
    return _tools().dispatch_tool(name, payload)


# ── coercion helpers (raise WriteValidationError, never silently clip) ──

def _req_str(payload: dict, key: str) -> str:
    val = payload.get(key, "")
    text = str(val).strip() if val is not None else ""
    if not text:
        raise WriteValidationError(f"'{key}' is required.")
    return text


def _num(payload: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        raise WriteValidationError(f"'{key}' must be a number.")


def _int(payload: dict, key: str, default: int = 0) -> int:
    try:
        return int(float(payload.get(key, default)))
    except (TypeError, ValueError):
        raise WriteValidationError(f"'{key}' must be an integer.")


def _range(val: float, key: str, lo: float, hi: float) -> float:
    if not lo <= val <= hi:
        raise WriteValidationError(f"'{key}' must be between {lo} and {hi}.")
    return val


def _nonneg(val: float, key: str) -> float:
    if val < 0:
        raise WriteValidationError(f"'{key}' cannot be negative.")
    return val


def _ok(kind: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": True, "kind": kind, "message": message, **extra}


# ── primary write ops (one per life dimension + mood + dream) ──────────

def log_water(glasses: int = 1) -> dict[str, Any]:
    """Log water intake. Upstream owns reset-at-midnight + progress bar."""
    glasses = _int({"glasses": glasses}, "glasses", 1)
    _nonneg(glasses, "glasses")
    if glasses == 0:
        raise WriteValidationError("'glasses' must be at least 1.")
    return _ok("water", _dispatch("log_hydration", {"glasses": glasses}))


def log_sleep(hours: float, quality: int = 5, bedtime: str = "",
              wake_time: str = "", notes: str = "") -> dict[str, Any]:
    hours = _range(_num({"h": hours}, "h"), "hours", 0, 24)
    quality = int(_range(_num({"q": quality}, "q", 5), "quality", 1, 10))
    return _ok("sleep", _dispatch("log_sleep", {
        "hours": hours, "quality": quality, "bedtime": bedtime,
        "wake_time": wake_time, "notes": notes,
    }))


def log_meal(food: str, calories: float = 0, meal_time: str = "snack",
             protein_g: float = 0, carbs_g: float = 0,
             fat_g: float = 0, notes: str = "") -> dict[str, Any]:
    food = _req_str({"food": food}, "food")
    calories = _nonneg(_num({"c": calories}, "c"), "calories")
    if meal_time not in ("breakfast", "lunch", "dinner", "snack"):
        raise WriteValidationError(
            "'meal_time' must be breakfast/lunch/dinner/snack.")
    return _ok("nutrition", _dispatch("log_meal", {
        "food": food, "calories": calories, "meal_time": meal_time,
        "protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g,
        "notes": notes,
    }))


def log_workout(workout_type: str, duration_min: int,
                intensity: str = "medium",
                calories_burned: float = 0) -> dict[str, Any]:
    workout_type = _req_str({"workout_type": workout_type}, "workout_type")
    duration_min = _int({"d": duration_min}, "duration_min")
    _nonneg(duration_min, "duration_min")
    if intensity not in ("low", "medium", "high"):
        raise WriteValidationError(
            "'intensity' must be low/medium/high.")
    return _ok("fitness", _dispatch("log_workout", {
        "workout_type": workout_type, "duration_min": duration_min,
        "intensity": intensity, "calories_burned": calories_burned,
    }))


def log_focus(task: str, duration_min: int = 25, quality: int = 7,
              distractions: int = 0) -> dict[str, Any]:
    task = _req_str({"task": task}, "task")
    duration_min = _int({"d": duration_min}, "duration_min", 25)
    _nonneg(duration_min, "duration_min")
    quality = int(_range(_num({"q": quality}, "q", 7), "quality", 1, 10))
    return _ok("focus", _dispatch("log_focus_session", {
        "task": task, "duration_min": duration_min, "quality": quality,
        "distractions": distractions,
    }))


def log_stress(score: int, trigger: str = "") -> dict[str, Any]:
    score = int(_range(_num({"s": score}, "s"), "score", 1, 10))
    return _ok("stress", _dispatch(
        "log_stress", {"score": score, "trigger": trigger}))


def log_meditation(duration_min: int = 10) -> dict[str, Any]:
    duration_min = _int({"d": duration_min}, "duration_min", 10)
    _nonneg(duration_min, "duration_min")
    return _ok("meditation", _dispatch(
        "log_meditation", {"duration_min": duration_min}))


def log_gratitude(items: list) -> dict[str, Any]:
    items = [str(i).strip() for i in (items or []) if str(i).strip()]
    if not items:
        raise WriteValidationError("'items' needs at least one entry.")
    return _ok("gratitude", _dispatch("log_gratitude", {"items": items}))


def log_mood(state: str, severity: int = 5, note: str = "",
             mood: float | None = None) -> dict[str, Any]:
    """Name the weather. Persists as a typed mood memory (check-ins and
    mood entries are the same stream the mirror reads)."""
    state = _req_str({"state": state}, "state").lower()
    severity = int(_range(_num({"s": severity}, "s", 5), "severity", 1, 10))
    entry: dict[str, Any] = {"type": "mood", "state": state,
                             "severity": severity, "content": note or state}
    if mood is not None:
        entry["mood"] = _range(float(mood), "mood", 1, 10)
    return _ok("mood", _dispatch("remember", entry))


def log_dream(content: str, emotions: list | None = None,
              symbols: list | None = None, tone: str = "neutral",
              vividness: int = 5) -> dict[str, Any]:
    content = _req_str({"content": content}, "content")
    if tone not in ("positive", "neutral", "negative", "lucid", "nightmare"):
        raise WriteValidationError("Unknown dream 'tone'.")
    vividness = int(_range(_num({"v": vividness}, "v", 5),
                           "vividness", 1, 10))
    return _ok("dream", _dispatch("log_dream", {
        "content": content, "emotions": emotions or [],
        "symbols": symbols or [], "tone": tone, "vividness": vividness,
    }))


def log_note(content: str, entry_type: str = "note") -> dict[str, Any]:
    content = _req_str({"content": content}, "content")
    return _ok(entry_type, _dispatch(
        "remember", {"type": entry_type, "content": content}))


# ── quiet dimensions: spending, social, substance, reading, medication ──
# These join Life as calm cards (no flames, no punish): money-anxiety
# calm, connection, lever-view, stillness, and care. Upstream owns the
# stores; the whisper layer decides when any of it is worth surfacing.

def log_spending(amount: float, category: str = "uncategorized",
                 notes: str = "") -> dict[str, Any]:
    amount = _nonneg(_num({"amount": amount}, "amount"), "amount")
    return _ok("spending", _dispatch("log_expense", {
        "amount": amount, "category": category.strip() or "uncategorized",
        "notes": notes,
    }))


def log_social(with_who: str, quality: int = 5, duration_min: int = 0,
               notes: str = "") -> dict[str, Any]:
    with_who = _req_str({"with_who": with_who}, "with_who")
    quality = int(_range(_num({"quality": quality}, "quality", 5),
                         "quality", 1, 10))
    duration_min = _int({"duration_min": duration_min}, "duration_min")
    _nonneg(duration_min, "duration_min")
    return _ok("social", _dispatch("log_social_interaction", {
        "with_who": with_who, "quality": quality,
        "duration_min": duration_min, "notes": notes,
    }))


def log_substance(substance: str, amount: float = 0, unit: str = "",
                  notes: str = "") -> dict[str, Any]:
    substance = _req_str({"substance": substance}, "substance")
    amount = _nonneg(_num({"amount": amount}, "amount"), "amount")
    return _ok("substance", _dispatch("log_substance", {
        "substance": substance, "amount": amount, "unit": unit,
        "notes": notes,
    }))


def log_reading(title: str, minutes: int = 0, pages: int = 0,
                total_pages: int | None = None,
                notes: str = "") -> dict[str, Any]:
    title = _req_str({"title": title}, "title")
    minutes = _int({"minutes": minutes}, "minutes")
    pages = _int({"pages": pages}, "pages")
    _nonneg(minutes, "minutes")
    _nonneg(pages, "pages")
    payload: dict[str, Any] = {"title": title, "minutes": minutes,
                               "pages": pages, "notes": notes}
    if total_pages is not None:
        payload["total_pages"] = _int({"total_pages": total_pages},
                                      "total_pages")
    return _ok("reading", _dispatch("log_reading", payload))


def log_medication(name: str, taken: bool = True,
                   notes: str = "") -> dict[str, Any]:
    name = _req_str({"name": name}, "name")
    return _ok("medication", _dispatch("log_medication", {
        "name": name, "taken": bool(taken), "notes": notes,
    }))


# ── habits & goals (upstream owns streaks, freezes, goal-metric linkage) ─

def update_habit(name: str, completed: bool = True,
                 use_freeze: bool = False) -> dict[str, Any]:
    name = _req_str({"habit_name": name}, "habit_name")
    return _ok("habit", _dispatch("update_habit", {
        "habit_name": name, "completed": bool(completed),
        "use_freeze": bool(use_freeze),
    }))


def update_goal(name: str, progress: float | None = None, note: str = "",
                deadline: str | None = None) -> dict[str, Any]:
    name = _req_str({"goal_name": name}, "goal_name")
    payload: dict[str, Any] = {"goal_name": name, "note": note}
    if progress is not None:
        payload["progress"] = _range(float(progress), "progress", 0, 100)
    if deadline:
        payload["deadline"] = deadline
    return _ok("goal", _dispatch("update_goal", payload))


# ── relief outcomes (the personalization fuel for the ranking engine) ───

def log_relief_outcome(name: str, state: str, severity_before: int,
                       severity_after: int | None = None,
                       effectiveness: int | None = None) -> dict[str, Any]:
    """Record what happened so the NEXT recommendation is more personal.
    Same ledger the engine reads (StoreLedger over the core store)."""
    from superapp.core import get_store
    from superapp.relief import complete_outcome
    from superapp.relief.ledger import StoreLedger

    if effectiveness is not None:
        _range(float(effectiveness), "effectiveness", 1, 5)
    complete_outcome(
        StoreLedger(get_store()), name=_req_str({"name": name}, "name"),
        state=_req_str({"state": state}, "state"),
        severity_before=int(severity_before),
        severity_after=(int(severity_after)
                        if severity_after is not None else None),
        effectiveness=(int(effectiveness)
                       if effectiveness is not None else None),
    )
    return _ok("relief", f"Outcome recorded for '{name}'.",
               name=name, state=state)


# ── corrections (bounded: explicit ids, explicit errors) ────────────────

def correct_entry(entry_id: str, updates: dict) -> dict[str, Any]:
    if not str(entry_id or "").strip():
        raise WriteValidationError("'entry_id' is required.")
    if not isinstance(updates, dict) or not updates:
        raise WriteValidationError("'updates' must be a non-empty object.")
    message = _dispatch("correct_entry",
                        {"entry_id": entry_id, "updates": updates})
    if message.startswith("No entry found"):
        raise WriteValidationError(message)
    return _ok("correct", message, entry_id=entry_id)


def delete_entry(entry_id: str) -> dict[str, Any]:
    if not str(entry_id or "").strip():
        raise WriteValidationError("'entry_id' is required.")
    message = _dispatch("delete_entry", {"entry_id": entry_id})
    if message.startswith("No entry found"):
        raise WriteValidationError(message)
    return _ok("delete", message, entry_id=entry_id)


# ── the one dispatcher: kind -> exactly one write op ────────────────────

def write(kind: str, payload: dict | None = None) -> dict[str, Any]:
    """Route a write by kind. The future FastAPI POST /life/log-dim calls
    this and nothing else; the CLI/chat loop calls this instead of
    dispatch_tool for all Life writes."""
    payload = dict(payload or {})
    k = str(kind or "").strip().lower()
    if k == "water":
        return log_water(**{a: payload[a] for a in ("glasses",)
                            if a in payload})
    if k == "sleep":
        return log_sleep(payload.get("hours", 0), **{
            a: payload[a] for a in
            ("quality", "bedtime", "wake_time", "notes") if a in payload})
    if k in ("nutrition", "meal"):
        return log_meal(payload.get("food", ""), **{
            a: payload[a] for a in
            ("calories", "meal_time", "protein_g", "carbs_g", "fat_g",
             "notes") if a in payload})
    if k in ("fitness", "workout"):
        return log_workout(payload.get("workout_type", ""), **{
            a: payload[a] for a in
            ("duration_min", "intensity", "calories_burned")
            if a in payload})
    if k == "focus":
        return log_focus(payload.get("task", ""), **{
            a: payload[a] for a in
            ("duration_min", "quality", "distractions") if a in payload})
    if k == "stress":
        return log_stress(payload.get("score", 5), **{
            a: payload[a] for a in ("trigger",) if a in payload})
    if k == "meditation":
        return log_meditation(**{
            a: payload[a] for a in ("duration_min",) if a in payload})
    if k == "gratitude":
        return log_gratitude(payload.get("items", []))
    if k in ("mood", "checkin"):
        return log_mood(payload.get("state", ""), **{
            a: payload[a] for a in
            ("severity", "note", "mood") if a in payload})
    if k == "dream":
        return log_dream(payload.get("content", ""), **{
            a: payload[a] for a in
            ("emotions", "symbols", "tone", "vividness") if a in payload})
    if k in ("note", "remember"):
        return log_note(payload.get("content", ""), **{
            a: payload[a] for a in ("entry_type",) if a in payload})
    if k in ("spending", "expense"):
        return log_spending(payload.get("amount", 0), **{
            a: payload[a] for a in
            ("category", "notes") if a in payload})
    if k == "social":
        return log_social(payload.get("with_who", ""), **{
            a: payload[a] for a in
            ("quality", "duration_min", "notes") if a in payload})
    if k == "substance":
        return log_substance(payload.get("substance", ""), **{
            a: payload[a] for a in
            ("amount", "unit", "notes") if a in payload})
    if k == "reading":
        return log_reading(payload.get("title", ""), **{
            a: payload[a] for a in
            ("minutes", "pages", "total_pages", "notes") if a in payload})
    if k == "medication":
        return log_medication(payload.get("name", ""), **{
            a: payload[a] for a in ("taken", "notes") if a in payload})
    if k == "habit":
        return update_habit(payload.get("name", payload.get("habit_name",
                                                             "")), **{
            a: payload[a] for a in
            ("completed", "use_freeze") if a in payload})
    if k == "goal":
        return update_goal(payload.get("name", payload.get("goal_name",
                                                            "")), **{
            a: payload[a] for a in
            ("progress", "note", "deadline") if a in payload})
    if k in ("relief", "outcome"):
        return log_relief_outcome(**{
            a: payload[a] for a in
            ("name", "state", "severity_before", "severity_after",
             "effectiveness") if a in payload})
    raise UnknownKindError(
        f"Unknown write kind: {kind!r}. Known: water, sleep, nutrition, "
        "fitness, focus, stress, meditation, gratitude, mood, dream, note, "
        "spending, social, substance, reading, medication, "
        "habit, goal, relief.")
