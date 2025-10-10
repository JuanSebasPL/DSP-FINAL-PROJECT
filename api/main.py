from typing import Any
from fastapi import FastAPI, HTTPException
from datetime import datetime
from schemas.predict_schema import InputData
from services.model_service import load_model, make_prediction, train_and_save_model
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
from sqlalchemy import create_engine, text
app = FastAPI(
    title="DSP Project API",
    description="Endpoints for training and predicting diabetes outcomes",
    version="1.0.0",
)

DB_CONN_STRING  = "postgresql+psycopg2://admin:admin@localhost:5432/airflow_db"
 
def _build_engine(url: str):
    try:
        return create_engine(
            url,
            future=True,
            pool_pre_ping=True,          # dropping dead connections
            pool_recycle=1800,           # avoiding stale TCP
            connect_args={"connect_timeout": 3},
        )
    except Exception as e:
        print(f"[DB WARN] engine init failed: {e}")
        return None
 
engine = _build_engine(DB_CONN_STRING)

def save_predictions_to_db(items: list[dict]) -> bool:
    
    if engine is None:
        print("[DB WARN] No database engine - skipping save")
        return False
    
    try:
        with engine.connect() as conn:
            for item in items:
                
                sql = text("""
                    INSERT INTO diabetes_data 
                    (pregnancies, glucose, bloodpressure, skinthickness, 
                     insulin, bmi, diabetespedigreefunction, age, 
                     prediction, timestamp, source)
                    VALUES 
                    (:pregnancies, :glucose, :bloodpressure, :skinthickness,
                     :insulin, :bmi, :diabetespedigreefunction, :age,
                     :prediction, :timestamp, :source)
                """)
                
                conn.execute(sql, {
                    "pregnancies": item.get("Pregnancies"),
                    "glucose": item.get("Glucose"),
                    "bloodpressure": item.get("BloodPressure"),
                    "skinthickness": item.get("SkinThickness"),
                    "insulin": item.get("Insulin"),
                    "bmi": item.get("BMI"),
                    "diabetespedigreefunction": item.get("DiabetesPedigreeFunction"),
                    "age": item.get("Age"),
                    "prediction": item.get("prediction"),
                    "timestamp": item.get("timestamp"),
                    "source": item.get("source"),
                })
            
            conn.commit()
            print(f"[DB] Saved {len(items)} predictions to database")
            return True
            
    except Exception as e:
        print(f"[DB ERROR] Failed to save predictions: {e}")
        return False

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
        # NEW: Save predictions to database
        save_predictions_to_db(items)
            
        # Return both (keeps backward compatibility with any client expecting only 'predictions')
        return {"predictions": preds, "items": items}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
