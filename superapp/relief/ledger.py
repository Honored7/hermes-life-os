"""Effectiveness ledger: what has actually helped THIS person.

Replaces the old substring scans (search_memory(f"intervention {name}"))
with a typed contract. Two implementations:

- InMemoryLedger — for tests and dry runs.
- StoreLedger — persists typed outcome rows through the core Store, so
  outcomes survive restarts and flow through backup/export like any
  other memory. Rows are still plain memory entries
  ({type: "intervention", intervention_name, state, severity_before,
  severity_after, effectiveness}) — filtered by exact field match,
  never by substring.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except (ValueError, TypeError):
        return None


class InMemoryLedger:
    """Ledger backed by a plain list. Test seam and dry-run default."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def log_outcome(
        self,
        *,
        name: str,
        state: str,
        severity_before: int,
        severity_after: int | None,
        effectiveness: int | None,
    ) -> None:
        self.rows.append({
            "intervention_name": name,
            "state": state,
            "severity_before": severity_before,
            "severity_after": severity_after,
            "effectiveness": effectiveness,
            "timestamp": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        })

    def effectiveness_for(self, name: str) -> float | None:
        vals = [
            r["effectiveness"] for r in self.rows
            if r["intervention_name"] == name
            and isinstance(r["effectiveness"], (int, float))
        ]
        return sum(vals) / len(vals) if vals else None

    def recent_uses(self, name: str, hours: int = 24) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        count = 0
        for r in self.rows:
            if r["intervention_name"] != name:
                continue
            ts = _parse_ts(r.get("timestamp", ""))
            if ts is not None and ts >= cutoff:
                count += 1
        return count


class StoreLedger:
    """Ledger persisted through the core Store (upstream memory journal)."""

    def __init__(self, store: Any):
        self._store = store

    def log_outcome(
        self,
        *,
        name: str,
        state: str,
        severity_before: int,
        severity_after: int | None,
        effectiveness: int | None,
    ) -> None:
        self._store.write_memory({
            "type": "intervention",
            "intervention_name": name,
            "state": state,
            "severity_before": severity_before,
            "severity_after": severity_after,
            "effectiveness": effectiveness,
        })

    def _rows_for(self, name: str) -> list[dict[str, Any]]:
        # Broad recall by name, then exact field match — never substring
        # trust (a multi-word "type + name" query is not contiguous in
        # the stored JSON, so it would silently match nothing).
        candidates = self._store.search_memory(name, limit=50)
        return [
            r for r in candidates
            if r.get("type") == "intervention"
            and r.get("intervention_name") == name
        ]

    def effectiveness_for(self, name: str) -> float | None:
        vals = [
            r["effectiveness"] for r in self._rows_for(name)
            if isinstance(r.get("effectiveness"), (int, float))
        ]
        return sum(vals) / len(vals) if vals else None

    def recent_uses(self, name: str, hours: int = 24) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        count = 0
        for r in self._rows_for(name):
            ts = _parse_ts(r.get("timestamp", ""))
            if ts is not None and ts >= cutoff:
                count += 1
        return count
