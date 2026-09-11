"""
Protocols — Chained intervention sequences for complex emotional states.

A protocol is a guided journey through multiple interventions with
wizard narration between each step. Protocols activate at higher
severity levels where a single intervention isn't enough.

Example:
    Anger (severity 8+) → Cold Water → 4-7-8 Breathing → Cooldown Walk → Check-in
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProtocolStep:
    """A single step in a protocol."""
    intervention_id: Optional[int]  # None for check-in / transition steps
    wizard_message: str
    is_check_in: bool = False
    duration_seconds: int = 0  # 0 = use intervention's default


@dataclass
class Protocol:
    """A chained sequence of interventions."""
    id: str
    name: str
    description: str
    trigger_state: str
    trigger_severity_min: int
    steps: tuple[ProtocolStep, ...]

    def matches(self, state: str, severity: int) -> bool:
        return state == self.trigger_state and severity >= self.trigger_severity_min

    @property
    def total_duration_seconds(self) -> int:
        return sum(s.duration_seconds for s in self.steps)


# ─── Protocol Definitions ─────────────────────────────────────────────

PROTOCOLS: dict[str, Protocol] = {}


def _register_protocol(p: Protocol) -> Protocol:
    PROTOCOLS[p.id] = p
    return p


# ── Anger Reset Protocol ──
_register_protocol(Protocol(
    id="anger_reset",
    name="Anger Reset",
    description="Cool the body, slow the breath, walk it off.",
    trigger_state="angry",
    trigger_severity_min=7,
    steps=(
        ProtocolStep(
            intervention_id=5,  # Cold Water on Wrists
            wizard_message=(
                "First things first — let's cool the body. "
                "Go to a sink. Cold water on both wrists, 30 seconds. "
                "Your heart rate will physically drop. Go."
            ),
        ),
        ProtocolStep(
            intervention_id=1,  # 4-7-8 Breathing
            wizard_message=(
                "Good. Your body is cooling down. "
                "Now let's slow the breath. 4-7-8 breathing. "
                "In for 4, hold for 7, out for 8. Four cycles. "
                "Follow the animation. I'll count with you."
            ),
        ),
        ProtocolStep(
            intervention_id=4,  # Cooldown Walk
            wizard_message=(
                "The fire is lower now. Let's walk the rest of it off. "
                "Ten minutes outside. No phone. No rehearsing the argument. "
                "Just walk and let the air do its thing."
            ),
        ),
        ProtocolStep(
            intervention_id=None,
            is_check_in=True,
            wizard_message=(
                "Welcome back. You just did three things for yourself "
                "when you could have just stayed angry. That matters. "
                "Where's the anger now? 1 to 10. "
                "And — do you want to talk about what happened, "
                "or do you need a few more minutes of quiet?"
            ),
        ),
    ),
))

# ── Anxiety Spiral Protocol ──
_register_protocol(Protocol(
    id="anxiety_spiral",
    name="Anxiety Spiral Breaker",
    description="Ground, breathe, scan, process.",
    trigger_state="anxious",
    trigger_severity_min=7,
    steps=(
        ProtocolStep(
            intervention_id=6,  # Grounding 5-4-3-2-1
            wizard_message=(
                "Your mind is time-traveling to a future that hasn't happened. "
                "Let's pull you back to this room. "
                "5 things you see. 4 you hear. 3 you touch. 2 you smell. 1 you taste. "
                "I'll walk you through it. Just notice."
            ),
        ),
        ProtocolStep(
            intervention_id=2,  # Box Breathing
            wizard_message=(
                "You're back in the room. Good. "
                "Now let's steady the breath. Box breathing. "
                "In 4, hold 4, out 4, hold 4. Three minutes. "
                "Follow the square. I'm right here."
            ),
        ),
        ProtocolStep(
            intervention_id=7,  # Body Scan
            wizard_message=(
                "The breath is steadier. Now let's check the body. "
                "Where are you holding the anxiety? Jaw? Shoulders? Stomach? "
                "Let's do a quick body scan. Five minutes. "
                "Just notice. Don't fix. Notice."
            ),
        ),
        ProtocolStep(
            intervention_id=8,  # Journaling
            wizard_message=(
                "The body is softer. Now let's get the thoughts out. "
                "What triggered this? Write it down. No filter. "
                "Five minutes. Get the loop out of your head and onto paper."
            ),
        ),
        ProtocolStep(
            intervention_id=None,
            is_check_in=True,
            wizard_message=(
                "You just walked through four steps when you could have stayed in the spiral. "
                "That's not nothing. That's bravery. "
                "Where's the anxiety now? 1 to 10. "
                "And remember — the thing you're anxious about probably won't happen. "
                "And if it does, you'll handle it. You've handled hard things before."
            ),
        ),
    ),
))

# ── Overwhelm Reset Protocol ──
_register_protocol(Protocol(
    id="overwhelm_reset",
    name="Overwhelm Reset",
    description="Step out, breathe, prioritize, take one tiny step.",
    trigger_state="overwhelmed",
    trigger_severity_min=7,
    steps=(
        ProtocolStep(
            intervention_id=16,  # Step Outside
            wizard_message=(
                "You need to leave this room. Right now. "
                "Two minutes outside. Just stand there. Breathe. "
                "The walls are part of the overwhelm. Break the loop."
            ),
        ),
        ProtocolStep(
            intervention_id=2,  # Box Breathing
            wizard_message=(
                "Back? Good. Let's steady the system. "
                "Box breathing. In 4, hold 4, out 4, hold 4. "
                "Two minutes. Just breathe. Nothing else exists right now."
            ),
        ),
        ProtocolStep(
            intervention_id=14,  # Task Prioritization
            wizard_message=(
                "Now let's deal with the noise in your head. "
                "Dump every task, every worry, every 'I should' onto a list. "
                "All of them. Now cross out everything except ONE. "
                "The one that matters most today. Just one."
            ),
        ),
        ProtocolStep(
            intervention_id=15,  # 2-Minute Rule
            wizard_message=(
                "You've got your one thing. "
                "Now don't do the thing. Do the tiniest possible piece. "
                "Open the document. Put on your shoes. Pick up the phone. "
                "Two minutes. One tiny step. That's all."
            ),
        ),
        ProtocolStep(
            intervention_id=None,
            is_check_in=True,
            wizard_message=(
                "Look at what you just did. "
                "You went from 'everything is too much' to 'I did one thing.' "
                "That's the whole game. You don't have to do everything. "
                "You just have to do one thing. "
                "How are you feeling? 1 to 10."
            ),
        ),
    ),
))

# ── Sadness Support Protocol ──
_register_protocol(Protocol(
    id="sadness_support",
    name="Gentle Support",
    description="Acknowledge, connect, comfort, find light.",
    trigger_state="sad",
    trigger_severity_min=6,
    steps=(
        ProtocolStep(
            intervention_id=18,  # Self-Compassion Journaling
            wizard_message=(
                "I'm not going to tell you to cheer up. "
                "You're sad, and that's allowed. "
                "But I want you to try something: "
                "write down what you'd say to a friend who felt exactly this way. "
                "Then read it back to yourself. You deserve those words."
            ),
        ),
        ProtocolStep(
            intervention_id=17,  # Reach Out
            wizard_message=(
                "Sadness wants you alone. Don't let it win. "
                "One message. One person. 'Hey, how are you?' is enough. "
                "You don't have to explain. You just have to not be alone with this."
            ),
        ),
        ProtocolStep(
            intervention_id=11,  # Comfort Activity
            wizard_message=(
                "Now give yourself something soft. "
                "A warm drink. A favorite song. A comfort show. "
                "Full permission. No guilt. This is maintenance, not avoidance."
            ),
        ),
        ProtocolStep(
            intervention_id=9,  # Gratitude Logging
            wizard_message=(
                "Before we finish — three tiny things. "
                "Not big things. The coffee this morning. A song. The fact that you're here. "
                "Write them down. Feel each one for ten seconds. "
                "Your life isn't only the hard part. Even today."
            ),
        ),
        ProtocolStep(
            intervention_id=None,
            is_check_in=True,
            wizard_message=(
                "You just did four kind things for yourself on a hard day. "
                "That's not weakness. That's wisdom. "
                "I'm here tomorrow too. And the day after. "
                "You don't have to carry this alone. "
                "How are you feeling now? Even a small shift counts."
            ),
        ),
    ),
))

# ── Low Energy Protocol ──
_register_protocol(Protocol(
    id="low_energy_reboot",
    name="Energy Reboot",
    description="Hydrate, sunlight, move, rest if needed.",
    trigger_state="low_energy",
    trigger_severity_min=5,
    steps=(
        ProtocolStep(
            intervention_id=19,  # Hydration Check
            wizard_message=(
                "First: water. Full glass. Right now. "
                "If you haven't had water in two hours, "
                "half of this 'exhaustion' might just be dehydration. Go."
            ),
        ),
        ProtocolStep(
            intervention_id=20,  # Sunlight Exposure
            wizard_message=(
                "Now: sunlight. Five minutes. "
                "Go outside or stand by the brightest window. "
                "Photons on your skin. Serotonin boost. Free. Go."
            ),
        ),
        ProtocolStep(
            intervention_id=3,  # Physical Movement
            wizard_message=(
                "I know you're tired. Move anyway. "
                "Not a workout. Stretch. Walk to the corner. Ten jumping jacks. "
                "Three minutes. Your body needs to remember it's alive."
            ),
        ),
        ProtocolStep(
            intervention_id=None,
            is_check_in=True,
            wizard_message=(
                "Water, sun, movement. The holy trinity of 'I feel like a zombie.' "
                "How's the energy? Even 10% better is a win. "
                "If you're still running on empty, a 20-minute power nap might be the answer. "
                "Want me to set the timer?"
            ),
        ),
    ),
))

# ── Loneliness Protocol ──
_register_protocol(Protocol(
    id="loneliness_bridge",
    name="Connection Bridge",
    description="Reach out, write with compassion, comfort yourself.",
    trigger_state="lonely",
    trigger_severity_min=6,
    steps=(
        ProtocolStep(
            intervention_id=17,  # Reach Out
            wizard_message=(
                "One message. One person. Right now. "
                "'Hey, thinking of you.' That's enough. "
                "The loneliness is lying when it says nobody cares. "
                "Prove it wrong with one text. Press send."
            ),
        ),
        ProtocolStep(
            intervention_id=18,  # Self-Compassion Journaling
            wizard_message=(
                "While you wait — and even if they don't reply right away — "
                "I want you to write yourself a kind note. "
                "What would you say to a friend who felt this lonely? "
                "Write that. To yourself. You deserve it."
            ),
        ),
        ProtocolStep(
            intervention_id=11,  # Comfort Activity
            wizard_message=(
                "Now wrap yourself in something warm. "
                "A blanket. A favorite show. A warm drink. "
                "Being alone doesn't have to mean being uncomfortable. "
                "Make this moment soft."
            ),
        ),
        ProtocolStep(
            intervention_id=None,
            is_check_in=True,
            wizard_message=(
                "You reached out. You were kind to yourself. You made yourself comfortable. "
                "Loneliness is a signal, not a sentence. It means you need connection. "
                "And you just took three steps toward it. "
                "How's the loneliness now? 1 to 10."
            ),
        ),
    ),
))


# ─── Query Helpers ────────────────────────────────────────────────────

def get_protocol(state: str, severity: int) -> Optional[Protocol]:
    """
    Get the matching protocol for a state + severity, if one exists.
    Returns None if no protocol applies (single intervention is sufficient).
    """
    for protocol in PROTOCOLS.values():
        if protocol.matches(state, severity):
            return protocol
    return None


def get_all_protocols() -> list[Protocol]:
    """Get all defined protocols."""
    return list(PROTOCOLS.values())
