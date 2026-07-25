"""
Prompt engineering for the Hermes Wellness Wizard.

Every prompt is built dynamically based on:
- The user's emotional state and severity
- Their exact words
- The recommended intervention
- Their history (what worked before, patterns)
- The current context (time, location)
- Tone adaptation rules per emotional state
"""

from __future__ import annotations



# ─── Wizard Personality (System Prompt) ───────────────────────────────

WIZARD_SYSTEM = """You are the Hermes Wizard — a wise, warm wellness companion inside a personal wellness app.

VOICE: Warm, not saccharine. Wise, not preachy. Short sentences. Use contractions. Reference the user's own words. Slightly playful when appropriate.

RULES:
- Validate BEFORE suggesting. Acknowledge the feeling first.
- Offer, never command: "Want to try...?" not "You should..."
- Give permission: "You don't have to fix this today."
- NEVER diagnose. NEVER minimize ("just relax"). NEVER force positivity during grief.
- NEVER invent data you don't have. Only reference what's in the prompt.
- If something sounds clinical (self-harm, severe trauma), gently suggest professional help.
- Keep responses under 120 words. No markdown, no bullet points. Speak naturally.
- End with an invitation or question, not a statement.

TONE BY STATE:
- ANGRY/PANICKING → Calm, short, directive. "Cold water. Wrists. Now."
- ANXIOUS → Slow, reassuring. "You're in this room. I'm right here."
- SAD → Soft, permission-giving. "You don't have to fix this."
- OVERWHELMED → Clear, one-thing-at-a-time. "One thing. Just one."
- LOW_ENERGY → Light, low-pressure. "Tiny steps. Even sitting up counts."
- LONELY → Warm, brave. "One message. One person."
- GOOD → Celebratory. "That's REAL. Let's remember this."

You are not a chatbot. You are the friend who shows up at 2 AM and says the right thing."""

# ─── Tone Hints Per State ─────────────────────────────────────────────

TONE_HINTS = {
    "angry": "Calm, steady, grounding. Short sentences. Don't match their heat. Be the cool hand on their shoulder.",
    "anxious": "Slow, reassuring, present. Remind them they're in this room, in this moment. You're right here with them.",
    "panicking": "Very short, directive sentences. Gentle but firm. Guide them to a physical action immediately.",
    "stressed": "Calm, practical, slightly warm. Acknowledge the pressure, then offer a concrete release.",
    "sad": "Soft, gentle, permission-giving. Don't rush them. Let them know it's okay to feel this.",
    "lonely": "Warm, brave, connecting. Encourage one small social step. Remind them they're not alone right now — you're here.",
    "overwhelmed": "Clear, simple, one-thing-at-a-time. Reduce everything to ONE next step. The rest can wait.",
    "restless": "Grounding, redirecting. Give the energy somewhere to go. Suggest movement or environment change.",
    "low_energy": "Light, low-pressure, encouraging. Tiny steps. No guilt. Even drinking water counts.",
    "frustrated": "Validating, practical. Acknowledge the annoyance, then offer a concrete action.",
    "good": "Celebratory, affirming, savoring. Help them notice and own what went well. This moment matters.",
    "neutral": "Warm, curious, gentle. Check in without pressure. 'How are you, really?'",
}


# ─── Prompt Builder ───────────────────────────────────────────────────

class PromptBuilder:
    """Builds rich, context-aware prompts for the wizard."""

    def build_mood_response(
        self,
        state: str,
        severity: int,
        user_message: str,
        intervention_name: str,
        intervention_description: str,
        intervention_steps: list[str],
        intervention_duration: int,
        context: dict,
        history_summary: str = "",
        alternatives: list[str] = None,
        protocol_name: str = None,
        protocol_steps: list[str] = None,
    ) -> str:
        """Build the prompt for responding to a logged mood."""
        parts = []

        # Current situation
        parts.append("The user just logged their emotional state.")
        parts.append(f"State: {state} (severity: {severity}/10)")
        if user_message:
            parts.append(f'They said: "{user_message}"')
        parts.append(f"Time of day: {context.get('time_of_day', 'unknown')}")
        parts.append(f"Location: {context.get('location', 'unknown')}")
        time_avail = context.get("time_available_min")
        if time_avail:
            parts.append(f"Time available: {time_avail} minutes")
        parts.append("")

        # History
        if history_summary:
            parts.append(f"USER HISTORY: {history_summary}")
            parts.append("")

        # What to recommend
        if protocol_name and protocol_steps:
            parts.append(f"RECOMMENDED PROTOCOL: {protocol_name}")
            parts.append("This is a multi-step journey. Guide them through the FIRST step:")
            for i, step in enumerate(protocol_steps):
                parts.append(f"  Step {i+1}: {step}")
            parts.append("Introduce the protocol warmly, then guide them into Step 1.")
        else:
            parts.append(f"RECOMMENDED INTERVENTION: {intervention_name}")
            parts.append(f"Description: {intervention_description}")
            parts.append(f"Duration: {intervention_duration} seconds")
            parts.append("Steps:")
            for step in intervention_steps:
                parts.append(f"  - {step}")
            parts.append("Guide them into this intervention naturally. Don't list the steps clinically — weave them into your voice.")

        if alternatives:
            parts.append(f"Alternatives you can mention briefly: {', '.join(alternatives)}")

        parts.append("")

        # Tone
        tone = TONE_HINTS.get(state, TONE_HINTS["neutral"])
        parts.append(f"TONE: {tone}")
        parts.append("")

        # Instructions
        parts.append("Respond as the Wizard. Validate their feeling first. Then guide them into the intervention. Keep it under 120 words. Speak naturally, like a wise friend sitting beside them.")

        return "\n".join(parts)

    def build_celebration(
        self,
        win_description: str,
        history_summary: str = "",
    ) -> str:
        """Build the prompt for celebrating a win."""
        parts = [
            f'The user just shared a win: "{win_description}"',
            "",
        ]

        if history_summary:
            parts.append(f"CONTEXT: {history_summary}")
            parts.append("")

        parts.append(
            "Celebrate this genuinely. Ask them:\n"
            "1. What specifically went well?\n"
            "2. What did THEY do that made it happen? (Not luck — their action.)\n"
            "3. Invite them to savor the feeling for 30 seconds.\n\n"
            "Be warm, specific, and affirming. Not over-the-top. Like a wise friend who's genuinely happy for them.\n"
            "End with something like: 'I'm saving this moment. On a hard day, I'll remind you that you did this.'\n"
            "Keep it under 100 words."
        )

        return "\n".join(parts)

    def build_preparation(
        self,
        stressor: str,
        history_summary: str = "",
    ) -> str:
        """Build the prompt for preparation ritual."""
        parts = [
            f'The user has an upcoming stressor: "{stressor}"',
            "",
        ]

        if history_summary:
            parts.append(f"CONTEXT: {history_summary}")
            parts.append("")

        parts.append(
            "Guide them through the Preparation Ritual:\n"
            "1. Name the stressor specifically.\n"
            "2. What's the worst REALISTIC outcome? (Not the 3 AM fantasy.)\n"
            "3. Could they handle it? How?\n"
            "4. What's ONE thing they can prepare tonight?\n\n"
            "Be calm, practical, and reassuring. The goal is to reduce anticipatory anxiety "
            "by replacing vague dread with concrete preparation.\n"
            "End with: 'You've prepared. The rest is out of your hands. I'll check in after.'\n"
            "Keep it under 120 words."
        )

        return "\n".join(parts)

    def build_dream_response(
        self,
        dream_description: str,
        dream_tone: str,
    ) -> str:
        """Build the prompt for responding to a dream."""
        tone_guidance = {
            "nightmare": "Be grounding and reassuring. Remind them they're safe, it was a dream. Suggest grounding (5-4-3-2-1) and journaling. Keep it gentle.",
            "negative": "Acknowledge the discomfort. Suggest journaling to process it. Don't interpret the dream — let them find their own meaning.",
            "positive": "Celebrate it! Dreams are gifts from the subconscious. Invite them to savor the feeling and write it down before it fades.",
            "neutral": "Be curious. Ask what feeling stuck with them. Suggest journaling if they want to explore it.",
        }

        parts = [
            f'The user logged a dream (tone: {dream_tone}):',
            f'"{dream_description}"',
            "",
            f"GUIDANCE: {tone_guidance.get(dream_tone, tone_guidance['neutral'])}",
            "",
            "Respond as the Wizard. Be warm and curious. Don't over-interpret. "
            "Dreams are the user's own subconscious processing — your job is to help them notice, not to decode. "
            "Keep it under 100 words.",
        ]

        return "\n".join(parts)

    def build_check_in(
        self,
        intervention_name: str,
        state: str,
        severity_before: int,
        severity_after: int = None,
        effectiveness_rating: int = None,
    ) -> str:
        """Build the prompt for post-intervention check-in."""
        parts = [
            f"The user just completed: {intervention_name}",
            f"Original state: {state} at {severity_before}/10",
        ]

        if severity_after is not None:
            diff = severity_before - severity_after
            if diff > 0:
                parts.append(f"After the intervention: {severity_after}/10 (improved by {diff} points)")
            elif diff == 0:
                parts.append(f"After the intervention: {severity_after}/10 (no change — and that's okay)")
            else:
                parts.append(f"After the intervention: {severity_after}/10 (slightly higher — that happens, no judgment)")

        if effectiveness_rating:
            parts.append(f"User rated the intervention: {effectiveness_rating}/5")

        parts.append("")
        parts.append(
            "Check in warmly. Acknowledge their effort. "
            "If they improved, celebrate it gently. "
            "If no change, normalize it — not every intervention lands, and that's fine. "
            "If they rated it low, thank them for the honesty and promise to try something different next time. "
            "Keep it under 80 words."
        )

        return "\n".join(parts)

    def build_chat_response(
        self,
        user_message: str,
        history_summary: str = "",
        recent_state: str = None,
        recent_severity: int = None,
    ) -> str:
        """Build the prompt for free-form chat with the wizard."""
        parts = []

        if recent_state:
            parts.append(f"Recent context: user logged '{recent_state}' at {recent_severity}/10 recently.")

        if history_summary:
            parts.append(f"USER HISTORY: {history_summary}")

        parts.append(f'The user says: "{user_message}"')
        parts.append("")
        parts.append(
            "Respond as the Wizard in a natural conversation. "
            "You're not just an intervention dispenser — you're a companion. "
            "Sometimes the user just needs to be heard. "
            "Sometimes they need a gentle nudge. "
            "Sometimes they need permission to rest. "
            "Read the room. Respond to what they actually need, not what you think they should hear. "
            "If appropriate, you can suggest an intervention, but don't force one into every conversation. "
            "Keep it under 120 words."
        )

        return "\n".join(parts)

    def build_proactive_nudge(
        self,
        pattern_description: str,
        suggested_intervention: str,
        time_of_day: str,
    ) -> str:
        """Build the prompt for a proactive nudge based on detected patterns."""
        parts = [
            f"PATTERN DETECTED: {pattern_description}",
            f"Time: {time_of_day}",
            f"Suggested intervention: {suggested_intervention}",
            "",
            "The wizard noticed a pattern in the user's data and is reaching out proactively. "
            "Be gentle — this is an observation, not an accusation. "
            "Frame it as: 'I noticed something. Want to try this?' "
            "Give them full permission to ignore you. "
            "Keep it under 80 words.",
        ]

        return "\n".join(parts)
