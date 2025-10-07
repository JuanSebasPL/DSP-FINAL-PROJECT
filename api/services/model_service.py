import os
import pickle
import pandas as pd
from typing import Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

MODEL_PATH = "models/model.pkl"
DATA_PATH = "models/diabetes.csv"


def load_model() -> RandomForestClassifier | None:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    print("Model not found.")
    return None


def train_and_save_model() -> dict[str, Any]:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    if "Outcome" not in df.columns:
        raise ValueError("CSV must contain an 'Outcome' column for training.")

    x_train, x_test, y_train, y_test = train_test_split(
        df.drop("Outcome", axis=1),
        df["Outcome"],
        test_size=0.2,
        random_state=42,
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)

    preds = model.predict(x_test)
    acc = accuracy_score(y_test, preds)

    os.makedirs("models", exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"Model trained and saved (Accuracy: {acc:.2f})")
    return {"message": "Model created successfully", "accuracy": round(acc, 2)}


def make_prediction(model: RandomForestClassifier, data: list[dict]) -> list[int]:
    if model is None:
        return []

    df = pd.DataFrame(data)
    preds = model.predict(df)
    return preds.tolist()
