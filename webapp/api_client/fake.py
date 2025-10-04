# webapp/api_client/fake.py

import pandas as pd
import random
import time


class FakeAPIClient:
    """
    A fake API client that pretends to call a model service.
    It just makes up predictions so we can test the Streamlit UI.
    """

    def predict(self, rows: list[dict]) -> pd.DataFrame:
        """
        Pretend to make predictions for a list of rows (dictionaries).
        Each row is a dictionary like {"feature1": 10, "feature2": 5}.
        We will just return a random 0/1 prediction for each row.
        """

        # Simulate network delay
        time.sleep(1)

        results = []
        for row in rows:
            pred = 1 if sum(v for v in row.values() if isinstance(v, (int, float))) % 2 == 0 else 0
            # ^ silly rule: if sum of numeric values is even → 1, else 0
            results.append({**row, "prediction": pred, "source": "webapp"})

        return pd.DataFrame(results)
