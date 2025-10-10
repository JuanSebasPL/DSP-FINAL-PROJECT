# webapp/api_client.py (simple version)

import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

def to_snake_case_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert UI keys (TitleCase) to API keys (snake_case)."""
    mapping = {
        "Pregnancies": "pregnancies",
        "Glucose": "glucose",
        "BloodPressure": "blood_pressure",
        "SkinThickness": "skin_thickness",
        "Insulin": "insulin",
        "BMI": "bmi",
        "DiabetesPedigreeFunction": "diabetes_pedigree_function",
        "Age": "age",
    }
    return {mapping.get(k, k): v for k, v in row.items()}

class DiabetesAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 30

    def health_check(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/", timeout=self.timeout)
        r.raise_for_status()
        return {"ok": True, "status": r.status_code}

    def predict(self, rows: List[Dict[str, Any]]) -> pd.DataFrame:
        """Send rows -> get predictions -> return DataFrame with extras."""
        # 1) prepare payload
        payload = {"data": [to_snake_case_row(r) for r in rows]}

        # 2) call API
        r = requests.post(f"{self.base_url}/predict", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()  # expects {"predictions": [0/1, ...]}

        # 3) build DataFrame: original rows + prediction + timestamp + source
        preds = data.get("predictions", [])
        if len(preds) != len(rows):
            raise ValueError("API returned different number of predictions than rows")

        df = pd.DataFrame(rows).copy()
        df["prediction"] = preds
        df["timestamp"] = datetime.utcnow().isoformat()
        df["source"] = "webapp"
        return df

    # optional stub to keep the Past Predictions page happy
    def get_past_predictions(self, *args, **kwargs) -> pd.DataFrame:
        cols = [
            "timestamp","Pregnancies","Glucose","BloodPressure","SkinThickness",
            "Insulin","BMI","DiabetesPedigreeFunction","Age","prediction","source"
        ]
        return pd.DataFrame(columns=cols)
