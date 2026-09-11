"""Relief layer — THE PRODUCT. Recovery methods live here, nowhere else.

Owns: intervention library, multi-step protocols, ranking engine
(severity-match + context fit + personal effectiveness + recency),
safety gateway (crisis backstop, injection shield), effectiveness
ledger. May import superapp.core + superapp.intelligence only.
"""

from superapp.relief.api import (
    Recommendation,
    ReliefLedger,
    ReliefNotMigratedError,
    ReliefResult,
    complete_outcome,
    recommend,
    relief_available,
)
from superapp.relief.engine import WellnessEngine
from superapp.relief.ledger import InMemoryLedger, StoreLedger
from superapp.relief.safety import (
    COMPANION_SYSTEM,
    gate,
    is_crisis,
    safety_response,
    wrap_user,
)

__all__ = [
    "COMPANION_SYSTEM",
    "InMemoryLedger",
    "Recommendation",
    "ReliefLedger",
    "ReliefNotMigratedError",
    "ReliefResult",
    "StoreLedger",
    "WellnessEngine",
    "complete_outcome",
    "gate",
    "is_crisis",
    "recommend",
    "relief_available",
    "safety_response",
    "wrap_user",
]
