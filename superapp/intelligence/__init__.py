"""Intelligence layer — read-only analytics over core.

Owns: pattern detection, Pearson correlations (incl. lagged), per-domain
summaries, consistency / time-of-day / day-of-week signals.
Reads core only. Never writes. Imports superapp.core (types) at most.
"""

from superapp.intelligence.patterns import (
    correlations,
    detect_patterns,
    pearson,
)

__all__ = ["correlations", "detect_patterns", "pearson"]
