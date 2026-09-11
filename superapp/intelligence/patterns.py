"""Read-only facades over demo/patterns.py and demo/analytics.py.

Upstream Turbox: demo/analytics.py provides compute_correlations() and
compute_lagged_correlations_multi(); demo/patterns.py:detect_patterns()
adds mood-dip / sleep-debt / stress / streak rules on top. Motif's
mirror()/climate() must consume these instead of reimplementing them
(relief migration step 2).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def _ensure_demo_on_path() -> None:
    demo_dir = str(Path(__file__).resolve().parent.parent.parent / "demo")
    if demo_dir not in sys.path:
        sys.path.insert(0, demo_dir)


def detect_patterns() -> dict[str, Any]:
    """Upstream detect_patterns(): trends + insights + correlation_details."""
    _ensure_demo_on_path()
    import patterns as upstream_patterns

    return upstream_patterns.detect_patterns()


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Shared Pearson r. None with fewer than 4 points or zero variance.

    The single implementation behind both upstream analytics and the
    experience mirror threads (which need n>=4 before claiming a thread).
    """
    if len(xs) < 4 or len(xs) != len(ys):
        return None
    _ensure_demo_on_path()
    import analytics as upstream_analytics

    return upstream_analytics.pearson_correlation(list(xs), list(ys))


def correlations(entries: list[dict] | None = None) -> list[dict[str, Any]]:
    """Pearson correlations over daily-averaged memory entries.

    With entries=None, uses the last 14 days (same window as
    detect_patterns). Returns [] when data is below thresholds
    (4+ overlapping days, |r| >= 0.4 upstream defaults).
    """
    _ensure_demo_on_path()
    if entries is None:
        import storage as upstream_storage

        entries = upstream_storage.get_recent_memory(days=14)
    import analytics as upstream_analytics

    return upstream_analytics.compute_correlations(entries)
