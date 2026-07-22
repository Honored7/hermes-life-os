"""
Optional integration hooks — wire the wizard into existing Hermes systems.
Add these to your scheduler or run them as cron jobs.
"""

from hermes.wizard import Wizard
from hermes.wellness.engine import WellnessEngine


def on_mood_logged(memory_store, llm_provider, state: str, severity: int, message: str = ""):
    """
    Hook: Called whenever the user logs a mood.
    Triggers the wizard to respond with an intervention if needed.
    """
    wizard = Wizard(memory_store=memory_store, llm_provider=llm_provider)
    response = wizard.respond_to_state(
        state=state,
        severity=severity,
        user_message=message,
    )
    return response


def on_pattern_detected(memory_store, llm_provider, pattern: dict):
    """
    Hook: Called when patterns.py detects a significant pattern.
    Example: "stress_spike_3days" → wizard proactively suggests an intervention.
    """
    wizard = Wizard(memory_store=memory_store, llm_provider=llm_provider)

    pattern_type = pattern.get("type", "")

    if "stress" in pattern_type:
        return wizard.respond_to_state(state="stressed", severity=7)
    elif "mood_dip" in pattern_type:
        return wizard.respond_to_state(state="sad", severity=6)
    elif "sleep_deprivation" in pattern_type:
        return wizard.respond_to_state(state="low_energy", severity=6)

    return None


def scheduled_check_in(memory_store, llm_provider, time_slot: str):
    """
    Hook: Called by the scheduler at 07:00, 12:00, 18:00, 23:00.
    Adds a wellness check-in to the existing briefing.
    """
    wizard = Wizard(memory_store=memory_store, llm_provider=llm_provider)

    if time_slot == "12:00":
        # Midday: check nutrition + stress
        nudge = wizard.nutrition_nudge()
        if nudge:
            return nudge

    elif time_slot == "23:00":
        # Evening: wind-down prompt
        return {
            "wizard_message": (
                "Hey, before you sleep — quick check. "
                "How was today? One word. "
                "And if there's anything on your mind for tomorrow, "
                "let's do a quick Preparation Ritual so you can sleep clean. "
                "Or if today was good — tell me one thing that went well. "
                "I want to celebrate it with you."
            ),
        }

    return None
