"""
Hermes Wellness Engine — Intervention system for the Life OS wizard.

This package adds active intervention capabilities to Hermes Life OS:
- 24 evidence-based wellness interventions
- State-matching engine with severity awareness
- Chained protocols for complex emotional states
- Feedback loop for per-user personalization
"""

# ── Core data (always available) ──────────────────────────────────────
from hermes.wellness.interventions import (
    Intervention,
    InterventionFamily,
    InterventionFormat,
    InterventionIntensity,
    EmotionalState,
    INTERVENTIONS,
    get_intervention,
    get_by_state,
    get_by_family,
    get_all,
)

# ── Engine (import safely) ────────────────────────────────────────────
try:
    from hermes.wellness.engine import WellnessEngine, EngineResult, Recommendation
except ImportError:
    WellnessEngine = None
    EngineResult = None
    Recommendation = None

# ── Protocols (import safely) ─────────────────────────────────────────
try:
    from hermes.wellness.protocols import PROTOCOLS, get_protocol, Protocol
except ImportError:
    PROTOCOLS = {}
    get_protocol = None
    Protocol = None

__all__ = [
    "Intervention",
    "InterventionFamily",
    "InterventionFormat",
    "InterventionIntensity",
    "EmotionalState",
    "INTERVENTIONS",
    "get_intervention",
    "get_by_state",
    "get_by_family",
    "get_all",
    "WellnessEngine",
    "EngineResult",
    "Recommendation",
    "PROTOCOLS",
    "get_protocol",
    "Protocol",
]
