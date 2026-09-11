"""Experience layer — presentation only. No math, no direct writes.

Owns: Today briefing (greeting + one true line + one suggestion),
Insights (mood weather/trend, mirror, climate cards + intelligence
signals), You keepsake + moments, Life dimension reads, sleep rhythm,
journal. All numbers come from the core store and intelligence facades;
all writes go through relief.complete_outcome() or the surfaces layer.
"""

from superapp.experience.briefing import alive, briefing
from superapp.experience.insights import (
    climate,
    get_effective_interventions,
    get_insights_summary,
    get_wins,
    mirror,
    mood_trend,
    mood_weather,
)
from superapp.experience.journal import (
    add_entry,
    delete_entry,
    list_entries,
    tag_entry,
)
from superapp.experience.keepsake import keepsake, moments
from superapp.experience.life_stats import dimension_stats
from superapp.experience.vitals import rhythm_payload, sleep_summary

__all__ = [
    "add_entry",
    "alive",
    "briefing",
    "climate",
    "delete_entry",
    "dimension_stats",
    "get_effective_interventions",
    "get_insights_summary",
    "get_wins",
    "keepsake",
    "list_entries",
    "mirror",
    "moments",
    "mood_trend",
    "mood_weather",
    "rhythm_payload",
    "sleep_summary",
    "tag_entry",
]
