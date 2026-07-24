"""
Hermes Life OS — Wellness Intervention System
===============================================
Adds active intervention capabilities to Hermes Life OS:
24 evidence-based interventions, 6 guided protocols,
an LLM-powered wizard that knows you and helps you heal.

Integrates with:
  - demo/llm_providers.py  (LLM client)
  - demo/storage.py        (memory + feedback loop)
  - demo/tools.py          (tool dispatch)
  - demo/patterns.py       (proactive triggers)
"""

from wellness.interventions import (
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
from wellness.engine import WellnessEngine
from wellness.protocols import PROTOCOLS, get_protocol, Protocol

__all__ = [
    "Intervention", "InterventionFamily", "InterventionFormat",
    "InterventionIntensity", "EmotionalState",
    "INTERVENTIONS", "get_intervention", "get_by_state", "get_by_family", "get_all",
    "WellnessEngine", "PROTOCOLS", "get_protocol", "Protocol",
]
