# Quiet dimensions — spending, social, substance, reading, medication.
#
# They join Life as calm cards: same {unit, target, lower_better, today,
# series, week, list} contract as the core nine, but the copy never
# punishes. Money gets averages, not alarms; substances get lever-view,
# not shame; missed doses get care, not red. The whisper layer decides
# when any of it is worth surfacing; these builders only report.
#
# Registry pattern: QUIET_DIMS maps name -> builder. Dimension #15 is a
# new entry here plus tests — never a new code path.

from __future__ import annotations

from datetime import date, timedelta

from superapp.experience import life_stats as _ls
from superapp.experience import store


def _today() -> str:
    return date.today().isoformat()


def _week_cut() -> str:
    return (date.today() - timedelta(days=7)).isoformat()


def spending() -> dict:
    entries = store.load_spending() or []
    today = _today()
    week = [e for e in entries if str(e.get("date", "")) >= _week_cut()]
    total_w = sum(_ls._num(e.get("amount")) for e in week)
    by_cat: dict[str, float] = {}
    for e in week:
        by_cat[e.get("category", "uncategorized")] = (
            by_cat.get(e.get("category", "uncategorized"), 0.0)
            + _ls._num(e.get("amount")))
    top = max(by_cat, key=by_cat.get) if by_cat else None
    return {
        "unit": "$", "target": None, "lower_better": False,
        "today": round(sum(_ls._num(e.get("amount")) for e in entries
                           if _ls._day(e) == today), 2),
        "series": _ls._series(entries, lambda e: _ls._num(e.get("amount"))),
        "week": {"total": round(total_w, 2),
                 "avg_per_day": round(total_w / 7, 2),
                 "top_category": top},
        "list": [f"{e.get('category', '')}: {e.get('amount', 0)}"
                 for e in entries[-5:]],
    }


def social() -> dict:
    entries = store.load_social() or []
    today = _today()
    week = [e for e in entries if str(e.get("date", "")) >= _week_cut()]
    quals = [_ls._num(e.get("quality")) for e in week
             if e.get("quality") is not None]
    return {
        "unit": "moments", "target": None, "lower_better": False,
        "today": sum(1 for e in entries if _ls._day(e) == today),
        "series": _ls._series(entries, lambda e: 1),
        "week": {"moments": len(week),
                 "avg_quality": round(sum(quals) / len(quals), 1)
                 if quals else None},
        "list": [str(e.get("with_who", "")) for e in entries[-5:]],
    }


def substance() -> dict:
    entries = store.load_substance() or []
    today = _today()
    week = [e for e in entries if str(e.get("date", "")) >= _week_cut()]
    by_sub: dict[str, int] = {}
    for e in week:
        by_sub[str(e.get("substance", "unknown"))] = (
            by_sub.get(str(e.get("substance", "unknown")), 0) + 1)
    return {
        "unit": "logs", "target": None, "lower_better": False,
        "today": sum(1 for e in entries if _ls._day(e) == today),
        "series": _ls._series(entries, lambda e: 1),
        "week": {"entries": len(week), "by_substance": by_sub},
        "list": [f"{e.get('substance', '')} {e.get('amount', '')} "
                 f"{e.get('unit', '')}".strip() for e in entries[-5:]],
    }


def reading() -> dict:
    entries = store.load_reading() or []
    today = _today()
    week = [e for e in entries if str(e.get("date", "")) >= _week_cut()]
    return {
        "unit": "min", "target": 20, "lower_better": False,
        "today": round(sum(_ls._num(e.get("minutes")) for e in entries
                           if _ls._day(e) == today), 1),
        "series": _ls._series(entries,
                              lambda e: _ls._num(e.get("minutes"))),
        "week": {"total_min": round(sum(_ls._num(e.get("minutes"))
                                       for e in week), 1),
                 "sessions": len(week),
                 "pages": int(sum(_ls._num(e.get("pages")) for e in week))},
        "list": [str(e.get("title", "")) for e in entries[-5:]],
    }


def medication() -> dict:
    entries = store.load_medication() or []
    today = _today()
    week = [e for e in entries if str(e.get("date", "")) >= _week_cut()]
    taken = sum(1 for e in week if e.get("taken", True))
    return {
        "unit": "doses", "target": None, "lower_better": False,
        "today": sum(1 for e in entries
                     if _ls._day(e) == today and e.get("taken", True)),
        "series": _ls._series(
            [e for e in entries if e.get("taken", True)], lambda e: 1),
        "week": {"taken": taken, "logged": len(week),
                 "adherence_pct": round(100 * taken / len(week))
                 if week else None},
        "list": [str(e.get("name", "")) for e in entries[-5:]],
    }


QUIET_DIMS = {
    "spending": spending,
    "social": social,
    "substance": substance,
    "reading": reading,
    "medication": medication,
}
