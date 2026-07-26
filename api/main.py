"""
Motif — Wellness Wizard API + PWA host + integrations.

Serves the API, the integrations OAuth endpoints, and the built PWA from a
single origin. Build the frontend first:  cd anima-app && npm run build
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demo"))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass  # no loader installed -> rely on the shell environment


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router
from api.integrations_routes import router as integrations_router
from wellness.interventions import INTERVENTIONS
from wellness.protocols import PROTOCOLS

app = FastAPI(
    title="Motif — Wellness Companion",
    description="A calm companion that notices the patterns of your life.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["wizard"])
app.include_router(integrations_router, prefix="/api/v1/integrations", tags=["integrations"])


@app.get("/api/v1/info")
async def info():
    return {
        "name": "Motif",
        "version": "0.4.0",
        "interventions": len(INTERVENTIONS),
        "protocols": len(PROTOCOLS),
    }


DIST = os.path.join(os.path.dirname(__file__), "..", "anima-app", "dist")

if os.path.isdir(DIST):
    _assets = os.path.join(DIST, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        candidate = os.path.join(DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(DIST, "index.html"))
else:
    @app.get("/")
    async def root():
        return JSONResponse({
            "name": "Motif API",
            "note": "Frontend not built yet. Run: cd anima-app && npm run build",
            "docs": "/docs",
        })
