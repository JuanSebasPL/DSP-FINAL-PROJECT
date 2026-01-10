import json
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
from api.schemas.predict_schema import InputData
from api.services.model_service import load_model, make_prediction, train_and_save_model
import pandas as pd
from fastapi import Body
from sqlalchemy import create_engine, text

app = FastAPI(
    title="DSP Project API",
    description="Endpoints for training and predicting diabetes outcomes",
    version="1.0.0",
)

DB_CONN_STRING = "postgresql+psycopg2://admin:admin@localhost:5432/airflow_db"


def _build_engine(url: str):
    try:
        return create_engine(
            url,
            future=True,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"connect_timeout": 3},
        )
    except Exception as e:
        print(f"[DB WARN] engine init failed: {e}")
        return None


engine = _build_engine(DB_CONN_STRING)


# -------------------------------------------------------------------
# Save predictions to database
# -------------------------------------------------------------------
def save_predictions_to_db(items: list[dict]) -> bool:
    if engine is None:
        print("[DB WARN] No database engine - skipping save")
        return False

    try:
        with engine.connect() as conn:
            for item in items:
                sql = text("""
                    INSERT INTO diabetes_data
                    (
                        pregnancies, glucose, bloodpressure, skinthickness,
                        insulin, bmi, diabetespedigreefunction, age,
                        prediction, actual_outcome, timestamp, source
                    )
                    VALUES
                    (
                        :pregnancies, :glucose, :bloodpressure, :skinthickness,
                        :insulin, :bmi, :diabetespedigreefunction, :age,
                        :prediction, :actual_outcome, :timestamp, :source
                    )
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
                    "actual_outcome": item.get("actual_outcome"),  # ✅ NEW
                    "timestamp": item.get("timestamp"),
                    "source": item.get("source"),
                })

            conn.commit()
            print(f"[DB] Saved {len(items)} predictions to database")
            return True

    except Exception as e:
        print(f"[DB ERROR] Failed to save predictions: {e}")
        return False


# -------------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------------
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
def predict(
    input_data: InputData,
    source: str = Query("webapp", description="Origin of the request, e.g. webapp or scheduled")
) -> dict[str, Any]:

    model = load_model()

    if model is None:
        return {"predictions": [], "message": "Model not found. Please train first."}

    try:
        df = pd.DataFrame(input_data.data)
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
            "outcome": "actual_outcome",
            "actualoutcome": "actual_outcome",
            "actual_outcome": "actual_outcome",
            "label": "actual_outcome",
            "y": "actual_outcome",
        }

        simplified = {c: c.lower().replace(" ", "").replace("_", "") for c in df.columns}
        rename_map = {c: alias[simplified[c]] for c in df.columns if simplified[c] in alias}
        df = df.rename(columns=rename_map)

        labels = None
        if "actual_outcome" in df.columns:
            labels = df["actual_outcome"].copy()

        expected = [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
        ]
        missing = [c for c in expected if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

        df_features = df[expected]

        preds = make_prediction(model, df_features)

        preds = [int(p) for p in preds]

        now_iso = datetime.utcnow().isoformat() + "Z"
        items = []

        for i, p in enumerate(preds):
            item = {
                **df_features.iloc[i].to_dict(),   # ✅ use df_features (only features)
                "prediction": p,
                "timestamp": now_iso,
                "source": source,
            }

            # ✅ attach label if provided
            if labels is not None:
                try:
                    item["actual_outcome"] = int(labels.iloc[i])
                except Exception:
                    item["actual_outcome"] = None

            items.append(item)

        save_predictions_to_db(items)

        return {"predictions": preds, "items": items}

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# -------------------------------------------------------------------
# FINAL & ONLY VALID saveStatistics ENDPOINT
# -------------------------------------------------------------------
@app.post("/saveStatistics", summary="Save file statistics", tags=["Statistics"])
def save_statistics_api(
    payload: dict = Body(...)
):
    """
    Receives statistics from Airflow and stores them in PostgreSQL
    """

    if engine is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        with engine.connect() as conn:
            sql = text("""
                INSERT INTO file_statistics
                (filename, nb_rows, nb_valid_rows, nb_invalid_rows, errors, timestamp)
                VALUES (:filename, :nb_rows, :nb_valid_rows, :nb_invalid_rows, :errors, :timestamp)
            """)

            conn.execute(sql, {
                "filename": payload["filename"],
                "nb_rows": payload["nb_rows"],
                "nb_valid_rows": payload["nb_valid_rows"],
                "nb_invalid_rows": payload["nb_invalid_rows"],
                "errors": json.dumps(payload.get("errors", [])),
                "timestamp": payload["timestamp"],
            })

            conn.commit()

        return {"status": "success", "message": "Statistics saved"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
