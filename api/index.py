
"""Vercel serverless entry point for the FastAPI app."""
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402


@app.middleware("http")
async def restore_rewritten_path(request, call_next):
    original_path = request.query_params.get("__original_path")

    if original_path and original_path.startswith("/api/"):
        request.scope["path"] = original_path
        request.scope["raw_path"] = original_path.encode("utf-8")

        params = [
            (key, value)
            for key, value in parse_qsl(
                request.scope.get("query_string", b"").decode("utf-8"),
                keep_blank_values=True,
            )
            if key != "__original_path"
        ]
        request.scope["query_string"] = urlencode(params).encode("utf-8")

    return await call_next(request)
