# webapp/pages/1_Prediction.py

import io
import time
import pandas as pd
import streamlit as st

from api_client import get_client

# --- SETTINGS (beginner-friendly) ---
REQUIRED_COLUMNS = ["feature1", "feature2"]  # keep it simple for now

client = get_client()


st.title("🔮 Prediction")
st.caption("Make single or batch (CSV) predictions — using a Fake API for now.")

# Small helper to standardize column names
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def validate_columns(df: pd.DataFrame, required: list[str]) -> tuple[list[str], list[str]]:
    cols = list(df.columns)
    missing = [c for c in required if c not in cols]
    extras = [c for c in cols if c not in required]
    return missing, extras

# ---------- SINGLE PREDICTION ----------
st.subheader("Single Prediction")

with st.form("single_prediction_form"):
    col1, col2 = st.columns(2)
    with col1:
        f1 = st.number_input("Feature 1 (number)", value=0.0, step=1.0, help="e.g., 10")
    with col2:
        f2 = st.number_input("Feature 2 (number)", value=0.0, step=1.0, help="e.g., 5")

    submit_button = st.form_submit_button("Predict")

    if submit_button:
        row = {"feature1": float(f1), "feature2": float(f2)}
        with st.spinner("Predicting..."):
            time.sleep(0.2)  # tiny pause so spinner is visible
            df_result = client.predict([row])
        st.success("Prediction complete.")
        st.dataframe(df_result, use_container_width=True)

st.divider()

# ---------- BATCH PREDICTION (CSV) ----------
st.subheader("Batch Prediction (CSV Upload)")

# Provide a tiny sample CSV to download
sample_df = pd.DataFrame(
    [{"feature1": 10, "feature2": 5}, {"feature1": 2, "feature2": 3}, {"feature1": 4, "feature2": 4}]
)
sample_csv_buf = io.StringIO()
sample_df.to_csv(sample_csv_buf, index=False)
st.download_button(
    label="⬇️ Download sample CSV",
    data=sample_csv_buf.getvalue(),
    file_name="sample_predictions.csv",
    mime="text/csv",
    help="Download a tiny CSV you can upload below."
)

uploaded_file = st.file_uploader("Upload CSV with columns: feature1, feature2", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

    df = normalize_columns(df)
    st.write("📄 Uploaded Data (first 50 rows):")
    st.dataframe(df.head(50), use_container_width=True)

    missing, extras = validate_columns(df, REQUIRED_COLUMNS)

    if missing:
        st.error(f"Missing required columns: {missing}. Please include these columns exactly: {REQUIRED_COLUMNS}")
    else:
        if extras:
            st.info(f"Note: Extra columns detected {extras}. They will be ignored by the fake predictor.")

        if st.button("Predict for CSV"):
            rows = df[REQUIRED_COLUMNS].to_dict(orient="records")
            with st.spinner("Predicting for CSV..."):
                df_result = client.predict(rows)
            st.success("Batch prediction complete.")
            st.dataframe(df_result, use_container_width=True)

            with st.expander("Dev tools: raw result (for debugging)"):
                st.write(df_result.to_dict(orient="records"))
