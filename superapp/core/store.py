"""Store facade over upstream demo/storage.py (+ crypto/users later).

Why a facade instead of importing storage directly everywhere:
- single seam for the v1.7 -> v1.30 storage upgrade (multi-profile,
  correct/delete, encryption) and for the future ReliefLedger;
- callers depend on the Store protocol, not on module-global paths;
- demo/* uses sys.path-relative imports, so the import happens lazily
  inside get_store(), never at module top level.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Protocol


class Store(Protocol):
    """Minimal persistence contract the whole superapp programs against."""

    def load_profile(self) -> dict: ...
    def save_profile(self, profile: dict) -> None: ...
    def load_habits(self) -> list: ...
    def save_habits(self, habits: list) -> None: ...
    def load_goals(self) -> list: ...
    def save_goals(self, goals: list) -> None: ...
    def write_memory(self, entry: dict[str, Any]) -> None: ...
    def search_memory(self, query: str, limit: int = 10) -> list[dict]: ...
    def get_recent_memory(self, days: int = 7) -> list[dict]: ...
    def memory_count(self) -> int: ...


class _UpstreamStore:
    """Store backed by demo/storage.py loaded with demo/ on sys.path."""

    def __init__(self, module: Any):
        self._m = module

    def load_profile(self) -> dict:
        return self._m.load_profile()

    def save_profile(self, profile: dict) -> None:
        self._m.save_profile(profile)

    def load_habits(self) -> list:
        return self._m.load_habits()

    def save_habits(self, habits: list) -> None:
        self._m.save_habits(habits)

    def load_goals(self) -> list:
        return self._m.load_goals()

    def save_goals(self, goals: list) -> None:
        self._m.save_goals(goals)

    def write_memory(self, entry: dict[str, Any]) -> None:
        self._m.write_memory(entry)

    def search_memory(self, query: str, limit: int = 10) -> list[dict]:
        return self._m.search_memory(query, limit=limit)

    def get_recent_memory(self, days: int = 7) -> list[dict]:
        return self._m.get_recent_memory(days=days)

    def memory_count(self) -> int:
        return self._m.memory_count()


def _demo_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "demo"


def get_store() -> Store:
    """Return the upstream-backed store. Lazy import by design (see above)."""
    demo_dir = str(_demo_dir())
    if demo_dir not in sys.path:
        sys.path.insert(0, demo_dir)
    import storage as upstream_storage

    return _UpstreamStore(upstream_storage)
