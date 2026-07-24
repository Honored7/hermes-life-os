"""
Hermes Life OS — Wellness API
===============================
FastAPI layer for the wellness wizard.
Run: uvicorn api.main:app --reload --port 8000
"""

import os
import sys

# Add demo/ to path so wellness modules can import storage, llm_providers, etc.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demo"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from wellness.interventions import INTERVENTIONS
from wellness.protocols import PROTOCOLS

app = FastAPI(
    title="Hermes Life OS — Wellness Wizard",
    description="A wise companion that helps you live better.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["wizard"])
app.include_router(router, tags=["wizard"])


@app.get("/")
async def root():
    return {
        "name": "Hermes Life OS — Wellness Wizard",
        "version": "0.2.0",
        "interventions": len(INTERVENTIONS),
        "protocols": len(PROTOCOLS),
        "docs": "/docs",
    }
