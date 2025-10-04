# webapp/api_client/fake.py

import random
import time
from typing import List, Dict, Any

import pandas as pd


class FakeAPIClient:
    """
    A fake API client that pretends to call a model service.
    It makes up predictions so we can test the Streamlit UI.
    """

    def predict(self, rows: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Make fake predictions for a list of rows (dicts).
        Rule: sum of numeric values -> even = 1, odd = 0
        """
        time.sleep(0.5)  # tiny delay to feel "real"
        results = []
        for row in rows:
            s = sum(v for v in row.values() if isinstance(v, (int, float)))
            pred = 1 if (s % 2 == 0) else 0
            results.append({**row, "prediction": pred, "source": "webapp"})
        return pd.DataFrame(results)

    def get_past_predictions(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
        source: str | None = None,
    ) -> pd.DataFrame:
        """
        Return a fake history table so you can build the Past Predictions page.
        We'll generate a few rows with timestamps, two sources (webapp/scheduled),
        and the same simple prediction rule.
        """
        now = pd.Timestamp.now()
        times = pd.date_range(end=now, periods=10, freq="5min")

        rows = []
        for i, ts in enumerate(times):
            f1 = random.randint(0, 10)
            f2 = random.randint(0, 10)
            pred = 1 if ((f1 + f2) % 2 == 0) else 0
            src = "webapp" if i % 2 == 0 else "scheduled"
            rows.append(
                {
                    "timestamp": ts,       # when prediction happened
                    "feature1": f1,
                    "feature2": f2,
                    "prediction": pred,
                    "source": src,
                }
            )

        df = pd.DataFrame(rows)

        # filters (simple, friendly)
        if source and source.lower() != "all":
            df = df[df["source"] == source]

        if start:
            try:
                start_ts = pd.to_datetime(start)
                df = df[df["timestamp"] >= start_ts]
            except Exception:
                pass

        if end:
            try:
                end_ts = pd.to_datetime(end) + pd.Timedelta(days=1)  # include the end day
                df = df[df["timestamp"] < end_ts]
            except Exception:
                pass

        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)
