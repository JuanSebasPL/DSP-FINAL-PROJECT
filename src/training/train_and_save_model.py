# src/training/train_and_save_model.py
import json
from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from joblib import dump

ROOT = Path(__file__).resolve().parents[2]  # repo root
DATA_PATH = ROOT / "data" / "diabetes.csv"
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]

print("Loading data from:", DATA_PATH)
df = pd.read_csv(DATA_PATH)

# Replace zeros with NaN where 0 is invalid
for col in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
    df[col] = df[col].replace(0, pd.NA)

df = df.fillna(df.median())

X = df[FEATURES]
y = df["Outcome"]

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=0.2)

model = RandomForestClassifier(n_estimators=100, random_state=42)
print("Training model...")
model.fit(X_train, y_train)

MODEL_PATH = MODELS_DIR / "diabetes_model.joblib"
dump(model, MODEL_PATH)
print("Saved model to:", MODEL_PATH)

FEATURES_PATH = MODELS_DIR / "features.json"
with open(FEATURES_PATH, "w") as f:
    json.dump(FEATURES, f)
print("Saved features list to:", FEATURES_PATH)
