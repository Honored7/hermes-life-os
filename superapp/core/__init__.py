"""Core layer — persistence and identity. Stdlib only.

Owns: profiles, JSON stores, append-only memory journal, schemas.
Imports nothing from superapp.* (enforced by skeleton test).
"""

from superapp.core.store import Store, get_store

__all__ = ["Store", "get_store"]
