"""Local HTTP surface for browsing and running verification obligations."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .obligations import OBLIGATIONS
from .reporting import result_to_dict, summarize
from .resources import web_dir
from .verifier import verify, verify_all


def create_app() -> FastAPI:
    app = FastAPI(
        title="Formal Security Verifier",
        version="0.2.0",
        description="Explicit-state and relational verification of security properties.",
    )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/obligations")
    def obligations() -> dict[str, Any]:
        return {
            "obligations": [
                {
                    "id": o.id,
                    "title": o.title,
                    "claim": o.claim,
                    "method": o.method.value,
                    "expect": o.expect.value,
                }
                for o in OBLIGATIONS
            ]
        }

    @app.post("/obligations/{obligation_id}/verify")
    def verify_one(obligation_id: str) -> dict[str, Any]:
        obligation = next((o for o in OBLIGATIONS if o.id == obligation_id), None)
        if obligation is None:
            raise HTTPException(status_code=404, detail="unknown obligation")
        return result_to_dict(verify(obligation))

    @app.get("/verify")
    def verify_everything() -> dict[str, Any]:
        return summarize(verify_all())

    directory = web_dir()
    if directory.exists():
        app.mount("/", StaticFiles(directory=str(directory), html=True), name="web")

    return app
