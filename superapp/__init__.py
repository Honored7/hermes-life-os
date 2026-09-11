"""Superapp — modular Life OS + Relief companion.

Layering (strict, enforced by tests/test_superapp_skeleton.py):
    core          — storage, profiles, schemas. Stdlib only, imports nothing
                    from superapp.*.
    intelligence  — read-only analytics over core (patterns, correlations,
                    summaries). May import superapp.core (types only).
    relief        — THE PRODUCT: interventions, protocols, ranking engine,
                    wizard/companion safety. May import core + intelligence.
    experience    — presentation only (briefing, climate/mirror, keepsake).
                    No math, no direct writes; calls relief/intelligence.
    surfaces      — thin shells (API routers, CLI, bots, scheduler workers).
                    No business logic; calls public facades.

No code moved yet: facades delegate lazily to demo/* where it exists.
demo imports always happen INSIDE functions (never top-level) because
upstream demo/* uses `sys.path`-relative imports (`from storage import`).
"""

__all__ = ["LAYERS", "__version__"]

__version__ = "0.1.0"

LAYERS = ("core", "intelligence", "relief", "experience", "surfaces")
