"""
Hermes Wellness API — FastAPI application.

Run:
    uvicorn hermes.api.main:app --reload --port 8000

Then open:
    http://localhost:8000/docs    ← Interactive API docs (Swagger UI)
    http://localhost:8000/health  ← Quick health check
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hermes.api.routes import router
from hermes.wellness.interventions import INTERVENTIONS
from hermes.wellness.protocols import PROTOCOLS

app = FastAPI(
    title="Hermes Wellness Wizard API",
    description=(
        "A wise companion that doesn't just track your life — "
        "it helps you live it better. 24 evidence-based interventions, "
        "6 guided protocols, personalized by LLM."
    ),
    version="0.1.0",
)

# CORS — allow frontend apps to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, prefix="/api/v1", tags=["wizard"])

# Also mount at root for convenience
app.include_router(router, tags=["wizard"])


@app.get("/")
async def root():
    return {
        "name": "Hermes Wellness Wizard",
        "version": "0.1.0",
        "interventions": len(INTERVENTIONS),
        "protocols": len(PROTOCOLS),
        "docs": "/docs",
        "health": "/health",
    }
