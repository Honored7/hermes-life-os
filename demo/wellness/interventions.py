"""
Intervention library for the Hermes Wellness Wizard.

Each intervention is a concrete, evidence-based action the wizard can
recommend. Every intervention includes:
- Which emotional states it helps
- Severity range where it's most effective (1-10)
- Duration, format, and requirements
- Step-by-step instructions
- Wizard voice lines (intro + outro)
- Contraindications (when NOT to suggest it)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ─── Enums ────────────────────────────────────────────────────────────

class EmotionalState(str, Enum):
    """Emotional states the wizard recognizes."""
    ANGRY = "angry"
    ANXIOUS = "anxious"
    STRESSED = "stressed"
    SAD = "sad"
    LONELY = "lonely"
    OVERWHELMED = "overwhelmed"
    RESTLESS = "restless"
    LOW_ENERGY = "low_energy"
    FRUSTRATED = "frustrated"
    PANICKING = "panicking"
    GOOD = "good"
    NEUTRAL = "neutral"


class InterventionFamily(str, Enum):
    """Categories of intervention."""
    BREATHWORK = "breathwork"
    MOVEMENT = "movement"
    GROUNDING = "grounding"
    MINDFULNESS = "mindfulness"
    COGNITIVE = "cognitive"
    SOCIAL = "social"
    COMFORT = "comfort"
    ENVIRONMENTAL = "environmental"
    NUTRITION = "nutrition"
    REST = "rest"
    CELEBRATION = "celebration"
    PREPARATION = "preparation"
    PHYSICAL_RESET = "physical_reset"


class InterventionFormat(str, Enum):
    """How the intervention is delivered in the app."""
    GUIDED_ANIMATION = "guided_animation"   # Breathing circle, visual timer
    AUDIO_GUIDED = "audio_guided"           # Narrated meditation / body scan
    TEXT_PROMPT = "text_prompt"             # Journaling prompt, cognitive exercise
    PHYSICAL = "physical"                   # Do something with your body / environment
    INTERACTIVE = "interactive"             # App-guided step-by-step (grounding)
    TIMER = "timer"                         # Simple countdown (power nap)


class InterventionIntensity(str, Enum):
    """How quickly the intervention takes effect."""
    IMMEDIATE = "immediate"     # < 1 minute (cold water, hydration)
    SHORT = "short"             # 1-5 minutes (breathing, grounding)
    MEDIUM = "medium"           # 5-15 minutes (walk, journaling, meditation)
    ONGOING = "ongoing"         # 15+ minutes or lifestyle (nature, nap, comfort)


# ─── Data Model ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class Intervention:
    """A single wellness intervention the wizard can recommend."""

    id: int
    name: str
    family: InterventionFamily
    description: str

    # Matching
    states: tuple[EmotionalState, ...]
    severity_range: tuple[int, int]          # (min, max) on 1-10 scale

    # Delivery
    duration_seconds: int
    format: InterventionFormat
    intensity: InterventionIntensity
    requires: tuple[str, ...] = ("nothing",)  # nothing, phone_down, outside, water, pen_paper, quiet_space

    # Content
    steps: tuple[str, ...] = ()
    wizard_intro: str = ""
    wizard_outro: str = ""

    # Safety
    contraindications: tuple[str, ...] = ()   # e.g., "panic_attack" → don't suggest long meditation

    # Metadata
    tags: tuple[str, ...] = ()

    def matches_state(self, state: str) -> bool:
        return any(s.value == state for s in self.states)

    def matches_severity(self, severity: int) -> bool:
        return self.severity_range[0] <= severity <= self.severity_range[1]

    def is_feasible(self, context: dict) -> bool:
        """Check if the user can do this right now given their context."""
        if "outside" in self.requires and not context.get("can_go_outside", True):
            return False
        if "quiet_space" in self.requires and not context.get("has_quiet_space", True):
            return False
        if "water" in self.requires and not context.get("has_water", True):
            return False
        if "pen_paper" in self.requires and not context.get("has_pen_paper", True):
            return False
        time_available = context.get("time_available_min", 999)
        if self.duration_seconds / 60 > time_available:
            return False
        return True


# ─── The 24 Interventions ─────────────────────────────────────────────

INTERVENTIONS: dict[int, Intervention] = {}


def _register(iv: Intervention) -> Intervention:
    INTERVENTIONS[iv.id] = iv
    return iv


# 1 ─ 4-7-8 Breathing
_register(Intervention(
    id=1,
    name="4-7-8 Breathing",
    family=InterventionFamily.BREATHWORK,
    description="Inhale 4s, hold 7s, exhale 8s. Activates the parasympathetic nervous system.",
    states=(EmotionalState.ANGRY, EmotionalState.ANXIOUS, EmotionalState.STRESSED, EmotionalState.PANICKING),
    severity_range=(5, 10),
    duration_seconds=120,
    format=InterventionFormat.GUIDED_ANIMATION,
    intensity=InterventionIntensity.SHORT,
    requires=("nothing",),
    steps=(
        "Sit or stand comfortably. Place the tip of your tongue behind your upper front teeth.",
        "Exhale completely through your mouth, making a whoosh sound.",
        "Close your mouth. Inhale quietly through your nose for 4 seconds.",
        "Hold your breath for 7 seconds.",
        "Exhale completely through your mouth for 8 seconds, making a whoosh sound.",
        "That's one cycle. Repeat 3 more times (4 cycles total).",
    ),
    wizard_intro=(
        "Let's slow everything down for two minutes. "
        "We're going to do 4-7-8 breathing — in for 4, hold for 7, out for 8. "
        "It's like a brake pedal for your nervous system. "
        "You don't have to fix anything right now. Just breathe with me."
    ),
    wizard_outro=(
        "Nice. Four cycles done. "
        "How's the body feeling compared to two minutes ago? "
        "Even a small shift counts. Rate it for me — 1 to 10, where are you now?"
    ),
    contraindications=(),
    tags=("breathing", "nervous_system", "quick", "anywhere"),
))

# 2 ─ Box Breathing
_register(Intervention(
    id=2,
    name="Box Breathing",
    family=InterventionFamily.BREATHWORK,
    description="Inhale 4s, hold 4s, exhale 4s, hold 4s. Used by Navy SEALs for stress regulation.",
    states=(EmotionalState.STRESSED, EmotionalState.OVERWHELMED, EmotionalState.ANXIOUS),
    severity_range=(4, 9),
    duration_seconds=180,
    format=InterventionFormat.GUIDED_ANIMATION,
    intensity=InterventionIntensity.SHORT,
    requires=("nothing",),
    steps=(
        "Sit upright. Relax your shoulders away from your ears.",
        "Inhale through your nose for 4 seconds.",
        "Hold your breath for 4 seconds.",
        "Exhale through your mouth for 4 seconds.",
        "Hold empty for 4 seconds.",
        "That's one box. Repeat for 3 minutes.",
    ),
    wizard_intro=(
        "Box breathing. Four sides, four counts. "
        "In for 4, hold for 4, out for 4, hold for 4. "
        "It's quiet, you can do it at your desk, and nobody will even know. "
        "Three minutes. Let's go."
    ),
    wizard_outro=(
        "Three minutes of box breathing, done. "
        "Notice your shoulders — are they still up by your ears? Let them drop. "
        "How's the stress level now? Give me a number."
    ),
    contraindications=(),
    tags=("breathing", "discreet", "work_friendly", "quick"),
))

# 3 ─ Physical Movement
_register(Intervention(
    id=3,
    name="Physical Movement",
    family=InterventionFamily.MOVEMENT,
    description="Walk, pushups, stretching, any movement. Moves stress hormones out of the body.",
    states=(EmotionalState.ANGRY, EmotionalState.RESTLESS, EmotionalState.LOW_ENERGY, EmotionalState.FRUSTRATED),
    severity_range=(3, 8),
    duration_seconds=300,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.MEDIUM,
    requires=("nothing",),
    steps=(
        "Stand up. Right now. That's step one and it's the hardest.",
        "Pick one: 10 pushups, 20 jumping jacks, stretch your arms overhead for 30 seconds, or walk to the end of the block.",
        "Move for 3-5 minutes. Doesn't have to be intense. Just move.",
        "Notice how your body feels after. The energy has to go somewhere — give it a way out.",
    ),
    wizard_intro=(
        "Your body is holding onto something right now. "
        "The fastest way to process it isn't thinking — it's moving. "
        "Stand up. Do 10 pushups, stretch, walk to the corner — anything. "
        "Five minutes. Let the body do what it needs to do."
    ),
    wizard_outro=(
        "Good. You moved. That matters more than you think. "
        "Stress hormones literally leave the body through movement. "
        "How do you feel compared to five minutes ago?"
    ),
    contraindications=("physical_injury",),
    tags=("exercise", "body", "energy_release"),
))

# 4 ─ Cooldown Walk
_register(Intervention(
    id=4,
    name="Cooldown Walk",
    family=InterventionFamily.MOVEMENT,
    description="Slow walk outside, no phone. Lets anger metabolize naturally.",
    states=(EmotionalState.ANGRY, EmotionalState.FRUSTRATED),
    severity_range=(6, 10),
    duration_seconds=600,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.MEDIUM,
    requires=("outside", "phone_down"),
    steps=(
        "Leave your phone behind (or put it on silent in your pocket).",
        "Walk outside. Slowly. This isn't exercise — it's a cooldown.",
        "Don't rehearse the argument. Don't plan your comeback. Just walk.",
        "Notice the air temperature. The sounds. The sky.",
        "Walk for 10 minutes. Turn around when you're ready.",
    ),
    wizard_intro=(
        "You're hot right now. Not temperature — the anger kind. "
        "The best thing you can do is walk it off. Slowly. Outside. No phone. "
        "You don't need to solve anything on this walk. "
        "You just need to let the fire burn down. Ten minutes. Go."
    ),
    wizard_outro=(
        "Welcome back. "
        "Notice — the anger isn't gone, but it's probably quieter. "
        "That's the walk doing its job. "
        "Do you want to talk about what happened, or do you need a few more minutes?"
    ),
    contraindications=("unsafe_outside", "late_night"),
    tags=("walking", "outside", "anger_management", "phone_free"),
))

# 5 ─ Cold Water on Wrists
_register(Intervention(
    id=5,
    name="Cold Water on Wrists",
    family=InterventionFamily.PHYSICAL_RESET,
    description="Run cold water over inner wrists for 30 seconds. Triggers the mammalian dive reflex.",
    states=(EmotionalState.ANGRY, EmotionalState.PANICKING, EmotionalState.ANXIOUS),
    severity_range=(7, 10),
    duration_seconds=30,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.IMMEDIATE,
    requires=("water",),
    steps=(
        "Go to a sink. Turn on cold water.",
        "Place both wrists under the stream, inner side up.",
        "Let the cold water run over your wrists for 30 seconds.",
        "Breathe slowly while you do this.",
        "The cold triggers your dive reflex — your heart rate will physically slow down.",
    ),
    wizard_intro=(
        "Okay. Right now, go to a sink. Cold water. Both wrists, 30 seconds. "
        "This isn't a metaphor — cold water on your wrists triggers a reflex "
        "that literally slows your heart rate. Your body will calm down before your mind does. "
        "Go. I'll be here when you get back."
    ),
    wizard_outro=(
        "Back? Good. "
        "Feel that? Your heart rate just dropped. Your body is listening. "
        "Now that the alarm bell is quieter — what do you need next?"
    ),
    contraindications=("raynauds", "cold_sensitivity"),
    tags=("immediate", "body_hack", "panic", "dive_reflex"),
))

# 6 ─ Grounding 5-4-3-2-1
_register(Intervention(
    id=6,
    name="Grounding 5-4-3-2-1",
    family=InterventionFamily.GROUNDING,
    description="Name 5 things you see, 4 hear, 3 touch, 2 smell, 1 taste. Pulls you back to the present.",
    states=(EmotionalState.ANXIOUS, EmotionalState.OVERWHELMED, EmotionalState.PANICKING),
    severity_range=(5, 10),
    duration_seconds=120,
    format=InterventionFormat.INTERACTIVE,
    intensity=InterventionIntensity.SHORT,
    requires=("nothing",),
    steps=(
        "Look around. Name 5 things you can SEE. Say them out loud or type them.",
        "Now listen. Name 4 things you can HEAR.",
        "Touch something. Name 3 things you can FEEL — the chair, your clothes, the air.",
        "Smell. Name 2 things you can SMELL.",
        "Taste. Name 1 thing you can TASTE.",
        "You're here. In this room. In this moment. The spiral was a story. This is real.",
    ),
    wizard_intro=(
        "Your mind is spinning and it's pulling you into a future that hasn't happened yet. "
        "Let's come back to this room. Right now. "
        "We're going to do 5-4-3-2-1. Five things you see, four you hear, "
        "three you touch, two you smell, one you taste. "
        "I'll walk you through it. You just notice."
    ),
    wizard_outro=(
        "You're here. In this room. In this body. "
        "The anxiety was a time machine — it took you to a future that doesn't exist yet. "
        "You just pulled yourself back. "
        "How's the intensity now? 1 to 10."
    ),
    contraindications=(),
    tags=("grounding", "anxiety", "panic", "present_moment", "dbt"),
))

# 7 ─ Body Scan
_register(Intervention(
    id=7,
    name="Body Scan",
    family=InterventionFamily.MINDFULNESS,
    description="Slow attention through each body part, noticing and releasing tension.",
    states=(EmotionalState.ANXIOUS, EmotionalState.STRESSED),
    severity_range=(3, 8),
    duration_seconds=300,
    format=InterventionFormat.AUDIO_GUIDED,
    intensity=InterventionIntensity.MEDIUM,
    requires=("quiet_space",),
    steps=(
        "Lie down or sit comfortably. Close your eyes.",
        "Bring your attention to your toes. Notice any sensation. Don't change it. Just notice.",
        "Slowly move your attention up: feet, ankles, calves, knees, thighs.",
        "Continue up: hips, stomach, chest, back, shoulders.",
        "Notice your jaw, your forehead, the space between your eyebrows. These hold tension.",
        "Take one deep breath and imagine the tension leaving with the exhale.",
        "Open your eyes when you're ready.",
    ),
    wizard_intro=(
        "Let's do a body scan. Five minutes. "
        "You're going to slowly move your attention from your toes to the top of your head. "
        "You're not trying to relax — you're just noticing where you're holding things. "
        "Most people discover they've been clenching their jaw for an hour without knowing. "
        "Lie down if you can. Close your eyes. Let's start at the toes."
    ),
    wizard_outro=(
        "Welcome back. "
        "Where were you holding the most tension? Jaw? Shoulders? Stomach? "
        "That's useful data — that's where your stress lives. "
        "Next time you feel it building, you'll know where to check first."
    ),
    contraindications=("active_panic_attack",),  # Too slow for acute panic; use grounding first
    tags=("mindfulness", "body_awareness", "tension_release", "relaxation"),
))

# 8 ─ Journaling
_register(Intervention(
    id=8,
    name="Journaling",
    family=InterventionFamily.COGNITIVE,
    description="Write what you're feeling, no filter. Gets the loop out of your head and onto paper.",
    states=(EmotionalState.ANXIOUS, EmotionalState.SAD, EmotionalState.OVERWHELMED),
    severity_range=(3, 8),
    duration_seconds=300,
    format=InterventionFormat.TEXT_PROMPT,
    intensity=InterventionIntensity.MEDIUM,
    requires=("pen_paper",),
    steps=(
        "Open a blank page. Paper or phone notes — doesn't matter.",
        "Set a timer for 5 minutes.",
        "Write. No filter. No grammar. No one will read this.",
        "If you don't know what to write, start with: 'Right now I feel...'",
        "When the timer goes off, you can keep it, throw it away, or tear it up. The value was in the writing.",
    ),
    wizard_intro=(
        "Your thoughts are looping right now. The same three sentences, over and over. "
        "The fastest way to break the loop is to put it somewhere outside your head. "
        "Grab a pen, open a notes app — anything. "
        "Write for five minutes. No filter. No one reads this. "
        "Start with 'Right now I feel...' and just go."
    ),
    wizard_outro=(
        "Five minutes. You got it out. "
        "You don't have to solve anything you wrote. You just had to get it out of the loop. "
        "Do you want to keep it, or let it go? Either way is fine."
    ),
    contraindications=(),
    tags=("writing", "cognitive", "processing", "expressive"),
))

# 9 ─ Gratitude Logging
_register(Intervention(
    id=9,
    name="Gratitude Logging",
    family=InterventionFamily.COGNITIVE,
    description="List 3 things you're grateful for. Shifts attention from deficit to abundance.",
    states=(EmotionalState.SAD, EmotionalState.LONELY, EmotionalState.LOW_ENERGY),
    severity_range=(2, 6),
    duration_seconds=120,
    format=InterventionFormat.TEXT_PROMPT,
    intensity=InterventionIntensity.SHORT,
    requires=("nothing",),
    steps=(
        "Think of 3 things you're grateful for right now. They can be tiny.",
        "Write them down. Specific is better than general: 'the way the coffee smelled this morning' beats 'coffee.'",
        "For each one, take 10 seconds to actually feel it. Don't just list it — savor it.",
        "That's it. Three things. Felt, not just listed.",
    ),
    wizard_intro=(
        "I know things feel heavy right now. I'm not going to tell you to 'look on the bright side.' "
        "But I am going to ask you to find three small things. "
        "Not big things. Tiny things. The coffee this morning. A song you like. "
        "The fact that you're here, talking to me, trying. "
        "Write them down. And actually feel each one for ten seconds. That's the whole exercise."
    ),
    wizard_outro=(
        "Three things. You found them even on a hard day. "
        "That's not toxic positivity — that's evidence that your life isn't only the hard part. "
        "I'm logging these. On the next hard day, I might remind you of them."
    ),
    contraindications=("acute_grief",),  # Don't force gratitude during acute loss
    tags=("gratitude", "positive_psychology", "cognitive_shift"),
))

# 10 ─ Social Connection
_register(Intervention(
    id=10,
    name="Social Connection",
    family=InterventionFamily.SOCIAL,
    description="Text, call, or be near someone you trust. Breaks the isolation loop.",
    states=(EmotionalState.SAD, EmotionalState.LONELY),
    severity_range=(3, 8),
    duration_seconds=300,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.MEDIUM,
    requires=("nothing",),
    steps=(
        "Think of one person you trust. Just one.",
        "Send them a message. It can be simple: 'Hey, thinking of you.' or 'Can I call you for 5 minutes?'",
        "You don't have to explain everything. You just have to break the isolation.",
        "If you can't reach anyone right now, go be around people — a café, a park, a library.",
    ),
    wizard_intro=(
        "Loneliness lies to you. It tells you nobody wants to hear from you. "
        "That's the loneliness talking, not the truth. "
        "Pick one person. One. Send them a text. "
        "It doesn't have to be deep. 'Hey, how are you?' is enough. "
        "You don't have to perform being okay. You just have to not be alone with this."
    ),
    wizard_outro=(
        "You reached out. That took more courage than you think. "
        "How did it feel? Did they respond? "
        "Either way — you broke the loop. That's the win."
    ),
    contraindications=("social_anxiety_acute",),  # May need smaller steps first
    tags=("connection", "social", "isolation_break"),
))

# 11 ─ Comfort Activity
_register(Intervention(
    id=11,
    name="Comfort Activity",
    family=InterventionFamily.COMFORT,
    description="Favorite music, show, food, warm drink. Gentle self-soothing.",
    states=(EmotionalState.SAD, EmotionalState.STRESSED),
    severity_range=(2, 6),
    duration_seconds=600,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.ONGOING,
    requires=("nothing",),
    steps=(
        "Pick one thing that reliably makes you feel a little better.",
        "A favorite song. A comfort show. A warm drink. A soft blanket.",
        "Give yourself full permission to enjoy it. No guilt. No 'I should be doing something productive.'",
        "This isn't avoidance. This is refueling. You can't pour from an empty cup.",
    ),
    wizard_intro=(
        "You don't need to fix anything right now. "
        "Sometimes the most useful thing you can do is make yourself a warm drink, "
        "put on that song you love, and just... be soft for a while. "
        "Pick your comfort thing. Give yourself full permission. "
        "You've earned the rest."
    ),
    wizard_outro=(
        "How was that? "
        "You don't have to justify it. Comfort isn't weakness — it's maintenance. "
        "Feeling a little softer than ten minutes ago?"
    ),
    contraindications=(),
    tags=("self_care", "comfort", "soothing", "permission"),
))

# 12 ─ Meditation
_register(Intervention(
    id=12,
    name="Meditation",
    family=InterventionFamily.MINDFULNESS,
    description="Sit quietly, focus on breath or body. Trains the mind to observe without reacting.",
    states=(EmotionalState.STRESSED, EmotionalState.RESTLESS),
    severity_range=(3, 7),
    duration_seconds=300,
    format=InterventionFormat.AUDIO_GUIDED,
    intensity=InterventionIntensity.MEDIUM,
    requires=("quiet_space",),
    steps=(
        "Sit comfortably. Back straight, hands in your lap.",
        "Close your eyes or soften your gaze.",
        "Bring your attention to your breath. Don't change it. Just watch it.",
        "When your mind wanders (it will), gently bring it back. No judgment.",
        "That's the whole practice. Wander, notice, return. That's one rep.",
        "After 5 minutes, open your eyes slowly.",
    ),
    wizard_intro=(
        "Five minutes. That's all. "
        "Sit down, close your eyes, watch your breath. "
        "Your mind will wander. That's not failure — that's the exercise. "
        "Every time you notice and come back, that's one rep for your brain. "
        "You're not trying to empty your mind. You're just watching it. "
        "Five minutes. I'll time you."
    ),
    wizard_outro=(
        "Five minutes. You sat with your own mind and didn't run. "
        "That's harder than it sounds and more valuable than you know. "
        "How's the noise level in your head? Quieter? Same? Either way — you showed up."
    ),
    contraindications=("active_panic_attack", "acute_trauma_flashback"),
    tags=("meditation", "mindfulness", "breath_focus", "mental_training"),
))

# 13 ─ Nature Time
_register(Intervention(
    id=13,
    name="Nature Time",
    family=InterventionFamily.ENVIRONMENTAL,
    description="Go outside, look at the sky, feel the air. Perspective shift through scale.",
    states=(EmotionalState.STRESSED, EmotionalState.OVERWHELMED),
    severity_range=(3, 7),
    duration_seconds=600,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.ONGOING,
    requires=("outside",),
    steps=(
        "Go outside. A park, a garden, a street with trees — anywhere with sky.",
        "Look up. Actually look at the sky. Notice how big it is.",
        "Feel the air on your skin. Is it warm? Cold? Still? Breezy?",
        "Listen to the sounds that aren't human-made. Birds, wind, leaves.",
        "Stay for 10 minutes. You don't have to walk. You can just stand there and be small under a big sky.",
    ),
    wizard_intro=(
        "You need to be outside. Not for exercise — for perspective. "
        "Go look at the sky. Actually look at it. "
        "Your problem is real, but it's not the whole world. "
        "The sky doesn't know about your deadline. The birds don't care about your email. "
        "And that's the point. Ten minutes under something bigger than the stress. Go."
    ),
    wizard_outro=(
        "Welcome back. "
        "The problem is probably still there. But you're a little bigger than it now. "
        "The sky helped. It always does. "
        "Ready to tackle the next thing, or do you need a few more minutes?"
    ),
    contraindications=("unsafe_outside", "severe_weather"),
    tags=("nature", "outside", "perspective", "grounding"),
))

# 14 ─ Task Prioritization
_register(Intervention(
    id=14,
    name="Task Prioritization",
    family=InterventionFamily.COGNITIVE,
    description="Pick ONE thing, write it down. Breaks the paralysis of too many tasks.",
    states=(EmotionalState.OVERWHELMED,),
    severity_range=(5, 9),
    duration_seconds=120,
    format=InterventionFormat.TEXT_PROMPT,
    intensity=InterventionIntensity.SHORT,
    requires=("nothing",),
    steps=(
        "Dump everything in your head onto a list. Every task, every worry, every 'I should.'",
        "Look at the list. Now cross out everything except ONE thing.",
        "The one thing that, if you did it today, would make the biggest difference.",
        "Write it on a separate piece of paper. That's your only job right now.",
        "The rest of the list will be there tomorrow. It's not going anywhere.",
    ),
    wizard_intro=(
        "Everything feels urgent right now. It's not. "
        "Let's do this: dump every single task in your head onto a list. All of them. "
        "Now look at the list. Cross out everything except one. "
        "The one thing that matters most today. Just one. "
        "Write it down. That's your only job. The rest can wait. I promise."
    ),
    wizard_outro=(
        "One thing. That's all you have to do today. "
        "The other 15 things on the list? They'll survive until tomorrow. "
        "You just gave yourself permission to not do everything at once. "
        "How does that feel? Lighter?"
    ),
    contraindications=(),
    tags=("productivity", "overwhelm", "prioritization", "focus"),
))

# 15 ─ 2-Minute Rule
_register(Intervention(
    id=15,
    name="2-Minute Rule",
    family=InterventionFamily.COGNITIVE,
    description="Do the tiniest possible step right now. Breaks paralysis.",
    states=(EmotionalState.OVERWHELMED, EmotionalState.RESTLESS),
    severity_range=(4, 8),
    duration_seconds=120,
    format=InterventionFormat.TEXT_PROMPT,
    intensity=InterventionIntensity.IMMEDIATE,
    requires=("nothing",),
    steps=(
        "What's the thing you're avoiding?",
        "What's the smallest possible first step? Not the whole task — the tiniest step.",
        "Open the document. Put on your shoes. Pick up the phone. Open the email.",
        "Do that one tiny step. Right now. Two minutes.",
        "You don't have to finish. You just have to start. Starting is the hard part.",
    ),
    wizard_intro=(
        "You're stuck. I can feel it. "
        "Here's the trick: don't do the thing. Do the tiniest possible piece of the thing. "
        "Don't write the report — open the document. "
        "Don't go to the gym — put on your shoes. "
        "Don't make the call — pick up the phone. "
        "Two minutes. One tiny step. That's all I'm asking. Go."
    ),
    wizard_outro=(
        "You started. That's the whole victory. "
        "You don't have to finish right now. You just had to break the paralysis. "
        "And look — you did. "
        "Want to keep going, or is starting enough for now? Both are fine."
    ),
    contraindications=(),
    tags=("productivity", "paralysis", "micro_step", "momentum"),
))

# 16 ─ Step Outside
_register(Intervention(
    id=16,
    name="Step Outside",
    family=InterventionFamily.ENVIRONMENTAL,
    description="Just leave the room/building for 2 minutes. Breaks the environmental loop.",
    states=(EmotionalState.OVERWHELMED, EmotionalState.RESTLESS),
    severity_range=(4, 8),
    duration_seconds=120,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.IMMEDIATE,
    requires=("outside",),
    steps=(
        "Stand up.",
        "Walk to the door.",
        "Go outside. Just outside. You don't have to go far.",
        "Stand there for 2 minutes. Breathe. Look at something that isn't a screen.",
        "Come back when you're ready. The room will be the same. You'll be a little different.",
    ),
    wizard_intro=(
        "You need to leave this room. Not forever. Two minutes. "
        "Stand up. Walk to the door. Step outside. "
        "You don't have to go anywhere. Just stand outside and breathe. "
        "The walls are part of the loop right now. Break the loop. Two minutes. Go."
    ),
    wizard_outro=(
        "Back? Good. "
        "Notice — the problem didn't change, but the room feels a little different. "
        "That's because you changed. Even two minutes of different air resets the brain. "
        "Ready to try again?"
    ),
    contraindications=("unsafe_outside",),
    tags=("environment_change", "quick", "reset", "outside"),
))

# 17 ─ Reach Out
_register(Intervention(
    id=17,
    name="Reach Out",
    family=InterventionFamily.SOCIAL,
    description="Send one message to one person. Breaks the loneliness spiral with one small act.",
    states=(EmotionalState.LONELY,),
    severity_range=(4, 9),
    duration_seconds=60,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.IMMEDIATE,
    requires=("nothing",),
    steps=(
        "Open your phone. Open your messages.",
        "Pick one person. Just one. Someone you trust, or someone you've been meaning to talk to.",
        "Send one message. It can be: 'Hey, how are you?' or 'Thinking of you.' or 'Can we talk later?'",
        "Press send. That's it. You don't have to perform. You just have to reach.",
    ),
    wizard_intro=(
        "One message. One person. That's all. "
        "Open your phone. Pick someone. "
        "You don't have to say anything deep. 'Hey, how are you?' is enough. "
        "The loneliness is telling you nobody wants to hear from you. "
        "Prove it wrong with one text. Press send. I'll wait."
    ),
    wizard_outro=(
        "You pressed send. "
        "That tiny act just broke the isolation loop. "
        "Whether they reply in 5 minutes or 5 hours doesn't matter. "
        "You reached. That's the whole point. How do you feel?"
    ),
    contraindications=(),
    tags=("social", "loneliness", "connection", "small_step"),
))

# 18 ─ Self-Compassion Journaling
_register(Intervention(
    id=18,
    name="Self-Compassion Journaling",
    family=InterventionFamily.COGNITIVE,
    description="Write to yourself like you'd write to a friend. Replaces the inner critic.",
    states=(EmotionalState.LONELY, EmotionalState.SAD),
    severity_range=(3, 8),
    duration_seconds=300,
    format=InterventionFormat.TEXT_PROMPT,
    intensity=InterventionIntensity.MEDIUM,
    requires=("pen_paper",),
    steps=(
        "Think about what you're feeling right now. The hard thing.",
        "Now imagine your closest friend came to you and said they felt exactly this way.",
        "What would you say to them? Write that down.",
        "Now read it back. That's what you deserve to hear. From yourself.",
        "You are allowed to be as kind to yourself as you are to others.",
    ),
    wizard_intro=(
        "I want you to try something. "
        "Imagine your best friend came to you and said exactly what you're feeling right now. "
        "What would you say to them? You wouldn't say 'you're weak' or 'get over it.' "
        "You'd be kind. You'd be gentle. "
        "Write that down — what you'd say to them. "
        "And then read it back to yourself. You deserve those words too."
    ),
    wizard_outro=(
        "You just gave yourself the kindness you'd give a friend. "
        "That's not selfish. That's necessary. "
        "You can't be your own enemy and heal at the same time. "
        "How did it feel to read those words back?"
    ),
    contraindications=(),
    tags=("self_compassion", "journaling", "inner_critic", "kindness"),
))

# 19 ─ Hydration Check
_register(Intervention(
    id=19,
    name="Hydration Check",
    family=InterventionFamily.NUTRITION,
    description="Drink a full glass of water. Dehydration mimics and worsens low energy and brain fog.",
    states=(EmotionalState.LOW_ENERGY,),
    severity_range=(2, 6),
    duration_seconds=30,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.IMMEDIATE,
    requires=("water",),
    steps=(
        "Get a full glass of water.",
        "Drink it. Slowly. All of it.",
        "If you haven't had water in the last 2 hours, this might be a bigger deal than you think.",
        "Dehydration causes fatigue, brain fog, and irritability. Sometimes the fix is just water.",
    ),
    wizard_intro=(
        "Quick question: when's the last time you drank water? "
        "If it's been more than two hours, go drink a full glass right now. "
        "I'm not being your mom. Dehydration literally causes fatigue and brain fog. "
        "Sometimes the 'I'm exhausted' is actually 'I'm thirsty.' "
        "Go. Full glass. I'll wait."
    ),
    wizard_outro=(
        "Glass empty? Good. "
        "Give it 15 minutes. If the fog lifts a little, you just found your culprit. "
        "I'm logging your hydration. If this keeps happening, I'll remind you earlier."
    ),
    contraindications=(),
    tags=("hydration", "nutrition", "quick", "energy", "brain_fog"),
))

# 20 ─ Sunlight Exposure
_register(Intervention(
    id=20,
    name="Sunlight Exposure",
    family=InterventionFamily.ENVIRONMENTAL,
    description="Stand in sunlight for 5-10 minutes. Boosts serotonin and regulates circadian rhythm.",
    states=(EmotionalState.LOW_ENERGY, EmotionalState.SAD),
    severity_range=(2, 6),
    duration_seconds=300,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.MEDIUM,
    requires=("outside",),
    steps=(
        "Go outside or stand by a bright window.",
        "Let sunlight hit your skin and eyes (don't stare at the sun).",
        "Stay for 5-10 minutes.",
        "If it's morning, this sets your circadian clock for better sleep tonight.",
        "If it's afternoon, this is a natural energy boost better than coffee.",
    ),
    wizard_intro=(
        "You need sunlight. Not a metaphor — actual photons on your skin. "
        "Go outside or stand by the brightest window you can find. "
        "Five to ten minutes. "
        "Sunlight triggers serotonin production and resets your body clock. "
        "It's the cheapest antidepressant that exists. Go get some."
    ),
    wizard_outro=(
        "Ten minutes of sun. "
        "Your serotonin just got a boost and your circadian clock just got a reset. "
        "Notice the difference? Even a little? "
        "I'm tracking your sunlight exposure. On grey days, I'll remind you."
    ),
    contraindications=("sun_sensitivity", "extreme_heat"),
    tags=("sunlight", "circadian", "serotonin", "energy", "natural"),
))

# 21 ─ Power Nap
_register(Intervention(
    id=21,
    name="Power Nap",
    family=InterventionFamily.REST,
    description="15-20 minute nap with alarm. Restores alertness without sleep inertia.",
    states=(EmotionalState.LOW_ENERGY,),
    severity_range=(3, 7),
    duration_seconds=1200,
    format=InterventionFormat.TIMER,
    intensity=InterventionIntensity.ONGOING,
    requires=("quiet_space",),
    steps=(
        "Set an alarm for 20 minutes. Not 30. Not 60. Twenty.",
        "Lie down. Close your eyes. You don't have to fall asleep — just rest.",
        "If your mind races, focus on your breathing.",
        "When the alarm goes off, get up immediately. Splash water on your face.",
        "You'll feel groggy for 5 minutes. That's normal. It passes.",
    ),
    wizard_intro=(
        "You're running on empty. I can see it in your data. "
        "Here's what I'm prescribing: a 20-minute power nap. "
        "Not two hours. Twenty. Set the alarm. "
        "You don't even have to fall asleep — just lie down and close your eyes. "
        "Your brain will do a quick cleanup cycle. "
        "Twenty minutes. I'll wake you up."
    ),
    wizard_outro=(
        "Rise and shine. "
        "You might feel groggy for five minutes — that's sleep inertia, it passes. "
        "Splash some water on your face. "
        "How's the energy? Even 10% better is a win."
    ),
    contraindications=("insomnia", "late_evening"),  # Don't nap if it'll wreck tonight's sleep
    tags=("sleep", "rest", "energy", "recovery"),
))

# 22 ─ Change of Environment
_register(Intervention(
    id=22,
    name="Change of Environment",
    family=InterventionFamily.ENVIRONMENTAL,
    description="Move to a different room or space. Breaks the environmental trigger loop.",
    states=(EmotionalState.RESTLESS, EmotionalState.ANXIOUS),
    severity_range=(3, 7),
    duration_seconds=120,
    format=InterventionFormat.PHYSICAL,
    intensity=InterventionIntensity.IMMEDIATE,
    requires=("nothing",),
    steps=(
        "Stand up and leave the room you're in.",
        "Go to a different room, a different floor, a different building.",
        "Change the lighting. Open a window. Put on different music.",
        "Your brain associates environments with states. Change the environment, change the state.",
    ),
    wizard_intro=(
        "You're stuck in a loop and this room is part of it. "
        "Your brain has associated this space with this feeling. "
        "So leave the space. Go to a different room. Open a window. Change the lighting. "
        "It sounds too simple, but it works. New environment, new neural context. "
        "Move. Two minutes."
    ),
    wizard_outro=(
        "New room, new context. "
        "Notice how the feeling shifted a little just by changing where you are? "
        "Your environment is more powerful than you think. "
        "Feeling any different?"
    ),
    contraindications=(),
    tags=("environment", "context_switch", "quick", "reset"),
))

# 23 ─ Win Celebration
_register(Intervention(
    id=23,
    name="Win Celebration",
    family=InterventionFamily.CELEBRATION,
    description="Log what went well, savor it. Reinforces positive neural pathways.",
    states=(EmotionalState.GOOD,),
    severity_range=(1, 10),
    duration_seconds=120,
    format=InterventionFormat.INTERACTIVE,
    intensity=InterventionIntensity.SHORT,
    requires=("nothing",),
    steps=(
        "What went well today? Name it. Specifically.",
        "Why did it go well? What did YOU do that made it happen?",
        "Take 30 seconds to actually feel the good feeling. Don't rush past it.",
        "I'm logging this. On a hard day, I'll remind you that you did this.",
    ),
    wizard_intro=(
        "Hey. I see you. And I see that today was good. "
        "Don't scroll past this. Don't say 'it was fine.' "
        "Tell me what went well. Specifically. "
        "And here's the important part: what did YOU do that made it happen? "
        "You didn't just get lucky. You did something. Let's name it."
    ),
    wizard_outro=(
        "That's not nothing. That's real. "
        "You showed up and it worked and you're allowed to feel good about it. "
        "I'm saving this moment. Next Tuesday, when things are hard, "
        "I'm going to remind you that you did this. "
        "Savor it. You earned it."
    ),
    contraindications=(),
    tags=("celebration", "positive_reinforcement", "savoring", "resilience"),
))

# 24 ─ Preparation Ritual
_register(Intervention(
    id=24,
    name="Preparation Ritual",
    family=InterventionFamily.PREPARATION,
    description="Prep for a known upcoming stressor. Reduces anticipatory anxiety.",
    states=(EmotionalState.ANXIOUS, EmotionalState.STRESSED),
    severity_range=(1, 10),
    duration_seconds=300,
    format=InterventionFormat.TEXT_PROMPT,
    intensity=InterventionIntensity.MEDIUM,
    requires=("nothing",),
    steps=(
        "What's the upcoming thing that's stressing you out? Name it.",
        "What's the worst realistic outcome? (Not the worst fantasy — the worst realistic one.)",
        "Could you handle that outcome? How?",
        "What's ONE thing you can prepare tonight to make tomorrow easier?",
        "Do that one thing. Then let it go. You've prepared. The rest is out of your hands.",
    ),
    wizard_intro=(
        "I can see it coming. The thing you're dreading. "
        "Let's not pretend it's not there. Let's prepare for it. "
        "What's the worst realistic outcome? Not the 3 AM fantasy — the realistic one. "
        "Could you handle it? Probably. "
        "What's one thing you can do tonight to make tomorrow 10% easier? "
        "Do that one thing. Then let it go. You've done your part."
    ),
    wizard_outro=(
        "You prepared. That's more than most people do. "
        "The anticipatory anxiety was worse than the thing itself — it usually is. "
        "Tomorrow, you'll handle it. You've handled hard things before. "
        "I'll check in with you after. You've got this."
    ),
    contraindications=(),
    tags=("preparation", "anticipatory_anxiety", "proactive", "planning"),
))


# ─── Query Helpers ────────────────────────────────────────────────────

def get_intervention(intervention_id: int) -> Optional[Intervention]:
    """Get a single intervention by ID."""
    return INTERVENTIONS.get(intervention_id)


def get_by_state(state: str) -> list[Intervention]:
    """Get all interventions that help with a given emotional state."""
    return [iv for iv in INTERVENTIONS.values() if iv.matches_state(state)]


def get_by_family(family: InterventionFamily) -> list[Intervention]:
    """Get all interventions in a family."""
    return [iv for iv in INTERVENTIONS.values() if iv.family == family]


def get_all() -> list[Intervention]:
    """Get all interventions, sorted by ID."""
    return sorted(INTERVENTIONS.values(), key=lambda iv: iv.id)
