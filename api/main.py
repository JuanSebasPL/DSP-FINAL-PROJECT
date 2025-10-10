from typing import Any
from fastapi import FastAPI, HTTPException
from datetime import datetime
from schemas.predict_schema import InputData
from services.model_service import load_model, make_prediction, train_and_save_model
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

app = FastAPI(
    title="DSP Project API",
    description="Endpoints for training and predicting diabetes outcomes",
    version="1.0.0",
)

@app.get("/", summary="Root endpoint", tags=["System"])
def root() -> dict[str, str]:
    return {"message": "Welcome to DSP API"}


@app.post("/model/train", summary="Train and save model", tags=["Model"])
def train_model() -> dict[str, Any]:
    try:
        result = train_and_save_model()
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/predict", summary="Predict diabetes outcome", tags=["Prediction"])
def predict(input_data: InputData) -> dict[str, Any]:
    model: RandomForestClassifier | None = load_model()

    if model is None:
        return {"predictions": [], "message": "Model not found. Please train first."}

    try:
         # Build a DataFrame from the incoming rows
        df = pd.DataFrame(input_data.data)

        # Normalize/alias to expected model training columns
        df.columns = [c.strip() for c in df.columns]
        alias = {
            "pregnancies": "Pregnancies",
            "glucose": "Glucose",
            "bloodpressure": "BloodPressure",
            "blood_pressure": "BloodPressure",
            "skinthickness": "SkinThickness",
            "skin_thickness": "SkinThickness",
            "insulin": "Insulin",
            "bmi": "BMI",
            "diabetespedigreefunction": "DiabetesPedigreeFunction",
            "diabetes_pedigree_function": "DiabetesPedigreeFunction",
            "age": "Age",
        }
        # map by simplified key (lower/no spaces/underscores)
        simplified = {c: c.lower().replace(" ", "").replace("_", "") for c in df.columns}
        rename_map = {c: alias[simplified[c]] for c in df.columns if simplified[c] in alias}
        df = df.rename(columns=rename_map)

        expected = [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
        ]
        missing = [c for c in expected if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

        df = df[expected]
        #Predict 
        preds = make_prediction(model, df)  # update make_prediction to accept df OR pass df.to_dict('records')
        preds = [int(p) for p in preds] #JSON-Serializable
         # NEW: build detailed rows for the UI (timestamp + source + features)
        items = []
        now_iso = datetime.utcnow().isoformat()
        for i, p in enumerate(preds):
            items.append({
                **df.iloc[i].to_dict(),
                "prediction": p,
                "timestamp": now_iso,
                "source": "webapp",
            })

        # Return both (keeps backward compatibility with any client expecting only 'predictions')
        return {"predictions": preds, "items": items}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
# api/main.py
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host="postgres",  # Docker service name
        database="airflow_db",
        user="admin",
        password="admin"
    )