"""Surfaces layer — thin shells, no business logic.

Owns: FastAPI routers, CLI entry, bots (telegram/slack/discord/whatsapp),
scheduler workers, PWA contract. Every handler calls a public facade
(core/intelligence/relief/experience) and renders the result. The only
module here allowed near demo/* is writes.py, which routes every
mutation through exactly one upstream tool each.

The PWA (anima-app/) is the reference client: it consumes the frozen
/api/v1 OpenAPI contract only. The future real app reuses the same
contract — no logic moves into the frontend.
"""

from superapp.surfaces import keepers, rhythm, writes

__all__ = ["API_CONTRACT_VERSION", "keepers", "rhythm", "writes"]

API_CONTRACT_VERSION = "v1"
