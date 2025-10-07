# webapp/api_client/real.py
from __future__ import annotations
import os
from typing import List, Dict, Any
import pandas as pd
import requests

DEFAULT_TIMEOUT = 20  # seconds

class RealAPIClient:
    """
    Real HTTP client for your FastAPI service.
    Expects the API to implement:
      POST /predict           body: {"rows": [...], "source": "webapp"}
                              resp: {"predictions": [ {features..., "prediction": ..., "timestamp": "...", "source": "..."} ]}
      GET  /past-predictions  query: start, end, source
                              resp: {"items": [ ...same shape as above... ]}
      GET  /health            resp: {"status":"ok"} (optional for status check)
    """

    def __init__(self, base_url: str | None = None):
        base_url = base_url or os.getenv("FASTAPI_URL", "")
        self.base_url = base_url.rstrip("/")
        if not self.base_url:
            raise ValueError("FASTAPI_URL is empty. Set it in webapp/.env")

    # Optional convenience (you can call from app sidebar if you like)
    def health(self) -> dict:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def predict(self, rows: List[Dict[str, Any]]) -> pd.DataFrame:
        payload = {"rows": rows, "source": "webapp"}
        r = requests.post(f"{self.base_url}/predict", json=payload, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        preds = data.get("predictions", [])
        if not isinstance(preds, list):
            raise ValueError("API response missing 'predictions' list")
        return pd.DataFrame(preds)

    def get_past_predictions(
        self, *, start: str | None = None, end: str | None = None, source: str | None = None
    ) -> pd.DataFrame:
        params = {k: v for k, v in {"start": start, "end": end, "source": source}.items() if v}
        r = requests.get(f"{self.base_url}/past-predictions", params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        items = data.get("items", [])
        if not isinstance(items, list):
            raise ValueError("API response missing 'items' list")
        return pd.DataFrame(items)
