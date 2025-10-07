from typing import Any
from fastapi import FastAPI, HTTPException
from schemas.predict_schema import InputData
from services.model_service import load_model, make_prediction, train_and_save_model
from sklearn.ensemble import RandomForestClassifier

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
        preds = make_prediction(model, input_data.data)
        return {"predictions": preds}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
