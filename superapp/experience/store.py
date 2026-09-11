"""Storage seam for the experience layer — the ONLY place here that touches
demo/. Upstream demo/* uses sys.path-relative imports (`from storage
import ...`), so the demo dir joins sys.path lazily INSIDE functions,
never at import time (enforced by test_superapp_skeleton.py).

Attribute access is live (module __getattr__ delegates to the storage
module on every access), so tmp-HOME test isolation keeps working:
reload storage under a new HOME and the next call sees the new paths.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _storage():
    demo = str(Path(__file__).resolve().parent.parent.parent / "demo")
    if demo not in sys.path:
        sys.path.insert(0, demo)
    import storage

    return storage


def __getattr__(name: str):
    return getattr(_storage(), name)


def load_calendar_tokens() -> dict:
    """Connected calendar doors, {} when integrations are absent/broken."""
    try:
        demo = str(Path(__file__).resolve().parent.parent.parent / "demo")
        if demo not in sys.path:
            sys.path.insert(0, demo)
        from integrations.calendar_base import load_tokens

        return load_tokens() or {}
    except Exception:
        return {}
