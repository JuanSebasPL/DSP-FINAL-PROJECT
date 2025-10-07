# webapp/api_client/__init__.py
from __future__ import annotations
import os

from .fake import FakeAPIClient
from .real import RealAPIClient

def get_client():
    mode = os.getenv("API_CLIENT_MODE", "FAKE").upper()

    if mode == "REAL":
        # fail early if FASTAPI_URL is missing
        if not os.getenv("FASTAPI_URL"):
            raise RuntimeError("FASTAPI_URL is not set but API_CLIENT_MODE=REAL")
        return RealAPIClient()

    return FakeAPIClient()