# src/api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from joblib import load
from pathlib import Path
import json
import numpy as np
import pandas as pd
from datetime import datetime
import threading

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
MODEL_FILE = MODELS_DIR / "diabetes_model.joblib"
FEATURES_FILE = MODELS_DIR / "features.json"
PRED_CSV = ROOT / "predictions" / "predictions.csv"
PRED_CSV.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="HealthVision Diabetes Predictor")
lock = threading.Lock()

class PatientFeatures(BaseModel):
    PatientID: str = Field(..., example="P001")
    Pregnancies: float
    Glucose: float
    BloodPressure: float
    SkinThickness: float
    Insulin: float
    BMI: float
    DiabetesPedigreeFunction: float
    Age: float

model = None
FEATURES = []

@app.on_event("startup")
def load_model():
    global model, FEATURES
    try:
        model = load(MODEL_FILE)
        with open(FEATURES_FILE, "r") as f:
            FEATURES = json.load(f)
        print("Model and features loaded successfully!")
    except Exception as e:
        print("Error loading model:", e)
        model = None

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}

@app.post("/predict")
def predict(p: PatientFeatures):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    X = np.array([[float(getattr(p, f)) for f in FEATURES]], dtype=float)
    pred_class = int(model.predict(X)[0])
    prob = float(model.predict_proba(X).max())

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "PatientID": p.PatientID,
        "predicted": pred_class,
        "probability": prob,
    }
    for feat in FEATURES:
        record[feat] = float(getattr(p, feat))

    df = pd.DataFrame([record])
    with lock:
        header = not PRED_CSV.exists()
        df.to_csv(PRED_CSV, mode="a", header=header, index=False)

    return {"patient": p.PatientID, "predicted": pred_class, "probability": prob}

@app.get("/predictions")
def get_predictions(limit: int = 50):
    if not PRED_CSV.exists():
        return {"predictions": []}
    df = pd.read_csv(PRED_CSV)
    df = df.sort_values("timestamp", ascending=False).head(limit)
    return {"predictions": df.to_dict(orient="records")}
