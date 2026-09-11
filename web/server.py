"""Web server entry point."""

from __future__ import annotations

import os
import sys

import uvicorn

WEB_DIR = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    frontend_dir = os.path.join(WEB_DIR, "frontend")
    app_path = os.path.join(WEB_DIR, "backend", "app.py")

    # Add backend to path
    sys.path.insert(0, os.path.dirname(app_path))

    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    from app import app as api_app

    # Serve frontend
    @api_app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @api_app.get("/{full_path:path}")
    async def serve_static(full_path: str):
        file_path = os.path.join(frontend_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    port = int(os.environ.get("ADL_PORT", "8000"))
    print(f"Algorithm Discovery Lab running at http://localhost:{port}")
    uvicorn.run(api_app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
