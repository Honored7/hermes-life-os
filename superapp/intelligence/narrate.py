# Tier-2 narrator — "why is this so?", answered once, on request.
#
# The deterministic layers (cards, correlations, patterns) speak first;
# this speaks only when the user taps "why?" on an Insight card. The
# model receives ONLY the card's own facts plus corroborating signals —
# never raw journals, never other dimensions, never open-ended history.
# No GROQ_API_KEY (or chosen provider key) means an honest "unavailable",
# never a traceback, never filler. Crisis content cannot arrive here:
# the input is a data card, not a person speaking.

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


def _demo():
    demo = str(Path(__file__).resolve().parent.parent.parent / "demo")
    if demo not in sys.path:
        sys.path.insert(0, demo)


SYSTEM = (
    "You are the quiet voice of Motif, a calm wellbeing companion. "
    "Explain the ONE finding below in two or three short sentences, "
    "warmly and plainly, as if to a friend. Use ONLY the facts given — "
    "never invent history, causes, numbers, or advice beyond one small, "
    "kind next step. No markdown, no lists, no headers, no diagnosis, "
    "no medical claims. If the finding is good news, help them savor it; "
    "if it is hard news, pair it with hope."
)


def build_prompt(card: dict[str, Any], lens: str = "start",
                 signals: dict | None = None) -> str:
    """Grounding block: card facts first, corroboration second."""
    lines = [
        f"Finding: {card.get('finding', '')}",
        f"Proof: {card.get('proof', '')}",
        f"Meaning: {card.get('meaning', '')}",
        f"Tone: {card.get('tone', '')} (strength or attention)",
        f"Scope: {'last 30 days' if lens == '30' else 'since they began'}",
    ]
    corrs = (signals or {}).get("correlations") or []
    if corrs:
        top = corrs[0]
        lines.append(
            f"Engine corroboration: {top.get('metric_a')} x "
            f"{top.get('metric_b')}, r={top.get('r')} "
            f"over {top.get('n_days')} days.")
    patterns = (signals or {}).get("patterns") or []
    for insight in patterns[:2]:
        lines.append(f"Pattern note: {insight}")
    return "\n".join(lines)


def narrate(card: dict[str, Any], lens: str = "start",
            signals: dict | None = None,
            provider: str | None = None) -> dict[str, Any]:
    """Narrate one card. Returns {text, provider, model} or
    {unavailable, reason} — never raises on provider trouble."""
    _demo()
    try:
        from llm_providers import (ProviderError, default_model_for,
                                   get_client, resolve_provider)
    except ImportError as e:
        return {"unavailable": True,
                "reason": f"LLM infrastructure missing: {e}"}
    try:
        name = resolve_provider(provider) if provider else resolve_provider()
        if name == "ollama" and not (provider or os.environ.get(
                "LIFE_OS_PROVIDER")):
            # Auto-detect landed on local Ollama with no explicit choice;
            # narration prefers a capable remote model — say so honestly.
            if not os.environ.get("GROQ_API_KEY") and not os.environ.get(
                    "OPENAI_API_KEY") and not os.environ.get(
                    "ANTHROPIC_API_KEY") and not os.environ.get(
                    "OPENROUTER_API_KEY"):
                return {"unavailable": True,
                        "reason": "Set GROQ_API_KEY (free, for testing) or "
                                  "another provider key to enable narration."}
        client = get_client(name)
        model = os.environ.get("LIFE_OS_MODEL") or default_model_for(name)
    except Exception as e:  # ProviderError + clear config errors
        return {"unavailable": True, "reason": str(e)}
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user",
                       "content": build_prompt(card, lens, signals)}],
            max_tokens=160,
        )
        text = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return {"unavailable": True,
                "reason": f"Narration failed ({e}). Try again shortly."}
    if not text:
        return {"unavailable": True,
                "reason": "The narrator came back empty. Try again."}
    return {"text": text, "provider": name, "model": model}
