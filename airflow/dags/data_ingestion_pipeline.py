import os
import random
import shutil
import pandas as pd
from datetime import datetime, timedelta
import requests

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# ---------------------------------------------------------------------
# PATHS  (FINAL — DO NOT CHANGE)
# ---------------------------------------------------------------------
STATS_ENDPOINT = "http://localhost:8000/saveStatistics"
PREDICT_ENDPOINT = "http://localhost:8000/predict?source=scheduled"

# ABSOLUTE PATH TO YOUR PROJECT'S REAL DATA FOLDER
BASE_PATH = "/home/brk/projects/final_dsp_project/DSP-FINAL-PROJECT/data"

RAW_DIR = os.path.join(BASE_PATH, "raw-data")
GOOD_DIR = os.path.join(BASE_PATH, "good_data")
BAD_DIR = os.path.join(BASE_PATH, "bad_data")
REPORTS_DIR = os.path.join(BASE_PATH, "reports")

# Ensure folders exist
for d in [RAW_DIR, GOOD_DIR, BAD_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)


# Expected schema
EXPECTED_COLUMNS = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
]

EXPECTED_DTYPES = {
    "Pregnancies": "int",
    "Glucose": "int",
    "BloodPressure": "int",
    "SkinThickness": "int",
    "Insulin": "int",
    "BMI": "float",
    "DiabetesPedigreeFunction": "float",
    "Age": "int",
}

# ---------------------------------------------------------------------
# TASK 1 — READ DATA
# ---------------------------------------------------------------------
def read_random_file(**context):
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]

    if not files:
        raise ValueError("No files found in raw-data folder.")

    filename = random.choice(files)
    filepath = os.path.join(RAW_DIR, filename)

    df = pd.read_csv(filepath)

    # Delete after reading
    os.remove(filepath)

    context["ti"].xcom_push(key="filename", value=filename)
    context["ti"].xcom_push(key="dataframe", value=df.to_json())

    print(f"Read and deleted file: {filename}")


# ---------------------------------------------------------------------
# TASK 2 — VALIDATE DATA (schema + types per row)
# ---------------------------------------------------------------------
def validate_data(**context):
    df = pd.read_json(context["ti"].xcom_pull(key="dataframe"))

    errors_detected = set()
    good_rows = []
    bad_rows = []

    # 1. Column-level validation
    required_cols = EXPECTED_COLUMNS + ["Outcome"]

    # Missing columns
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        errors_detected.add("missing columns")

    # Extra columns
    extra_cols = [c for c in df.columns if c not in required_cols]
    if extra_cols:
        errors_detected.add("extra columns")

    # Wrong number of columns
    if len(df.columns) != len(required_cols):
        errors_detected.add("incorrect number of columns")

    # 2. Row-level validation
    for idx, row in df.iterrows():
        row_is_bad = False

        for col, dtype in EXPECTED_DTYPES.items():
            value = row.get(col)

            # Null or NaN
            if pd.isna(value):
                errors_detected.add("null or NaN value")
                row_is_bad = True
                continue

            # Datatype check
            try:
                if dtype == "int":
                    casted = int(value)
                elif dtype == "float":
                    casted = float(value)
            except:
                errors_detected.add("invalid datatype")
                row_is_bad = True
                continue

            if casted < 0:
                errors_detected.add("negative numeric value")
                row_is_bad = True

            if col == "Age" and not (0 <= casted <= 130):
                errors_detected.add("age out of range")
                row_is_bad = True

            if col == "Insulin" and not (0 <= casted <= 900):
                errors_detected.add("insulin out of range")
                row_is_bad = True

        outcome = row.get("Outcome")
        if pd.isna(outcome) or outcome not in [0, 1]:
            errors_detected.add("invalid outcome value")
            row_is_bad = True

        if row_is_bad:
            bad_rows.append(row)
        else:
            good_rows.append(row)

    validation_result = {
        "errors": ";".join(sorted(errors_detected)),
        "nb_rows": len(df),
        "nb_good": len(good_rows),
        "nb_bad": len(bad_rows),
        "has_errors": len(errors_detected) > 0,
        "good_df_json": pd.DataFrame(good_rows).to_json(),
        "bad_df_json": pd.DataFrame(bad_rows).to_json(),
    }

    context["ti"].xcom_push(key="validation", value=validation_result)


# ---------------------------------------------------------------------
# TASK 3 — SAVE STATISTICS
# ---------------------------------------------------------------------
def save_statistics(**context):
    validation = context["ti"].xcom_pull(key="validation")
    filename = context["ti"].xcom_pull(key="filename")

    payload = {
        "filename": filename,
        "nb_rows": validation["nb_rows"],
        "nb_valid_rows": validation["nb_good"],
        "nb_invalid_rows": validation["nb_bad"],
        "errors": validation["errors"],
        "timestamp": str(datetime.utcnow())
    }

    print("Sending statistics to API:", payload)

    try:
        response = requests.post(STATS_ENDPOINT, json=payload)
        response.raise_for_status()
        print("Statistics successfully sent:", response.json())
    except Exception as e:
        print("Error sending statistics:", str(e))
        raise


# ---------------------------------------------------------------------
# TASK 4 — SEND ALERTS + HTML REPORT
# ---------------------------------------------------------------------
def send_alerts(**context):
    validation = context["ti"].xcom_pull(key="validation")
    filename = context["ti"].xcom_pull(key="filename")

    report_path = os.path.join(REPORTS_DIR, f"{filename}_report.html")

    with open(report_path, "w") as f:
        f.write("<h1>Data Quality Report</h1>")
        f.write(f"<p>File: {filename}</p>")
        f.write(f"<p>Total Rows: {validation['nb_rows']}</p>")
        f.write(f"<p>Good Rows: {validation['nb_good']}</p>")
        f.write(f"<p>Bad Rows: {validation['nb_bad']}</p>")
        f.write(f"<p>Errors: {validation['errors']}</p>")

    print(f"Generated report: {report_path}")

    POWER_AUTOMATE_URL = (
        "https://default3534b3d7316c4bc99ede605c860f49."
        "d2.environment.api.powerplatform.com:443/powerautomate/automations/direct/"
        "workflows/86b84d99340e439a8ec7eda4788a9ecd/triggers/manual/"
        "paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig="
        "zY7ket8QdnSBVLSrRVMnBG8bcgEixVMrGKEBzW7UZLc"
    )

    if validation["has_errors"]:
        payload = {
            "filename": filename,
            "nb_rows": validation["nb_rows"],
            "nb_good": validation["nb_good"],
            "nb_bad": validation["nb_bad"],
            "errors": validation["errors"],
            "report_path": report_path,
            "alert": f"Data quality issues detected in {filename}"
        }

        try:
            response = requests.post(POWER_AUTOMATE_URL, json=payload)
            response.raise_for_status()
            print("Teams alert sent successfully")
        except Exception as e:
            print(f"Failed to send alert: {e}")

    context["ti"].xcom_push(key="report_path", value=report_path)


# ---------------------------------------------------------------------
# TASK 5 — SAVE FILE (good_data / bad_data / split)
# ---------------------------------------------------------------------
def save_file(**context):
    validation = context["ti"].xcom_pull(key="validation")
    filename = context["ti"].xcom_pull(key="filename")

    good_df = pd.read_json(validation["good_df_json"])
    bad_df = pd.read_json(validation["bad_df_json"])

    if validation["nb_bad"] == 0:
        good_df.to_csv(os.path.join(GOOD_DIR, filename), index=False)
        print(f"All rows good. Saved to good_data/{filename}")
        return

    if validation["nb_good"] == 0:
        bad_df.to_csv(os.path.join(BAD_DIR, filename), index=False)
        print(f"All rows bad. Saved to bad_data/{filename}")
        return

    good_df.to_csv(os.path.join(GOOD_DIR, f"good_{filename}"), index=False)
    bad_df.to_csv(os.path.join(BAD_DIR, f"bad_{filename}"), index=False)

    print(f"Split file saved: good_data/good_{filename}, bad_data/bad_{filename}")

def send_predictions(**context):
    validation = context["ti"].xcom_pull(key="validation")
    filename = context["ti"].xcom_pull(key="filename")

    good_df = pd.read_json(validation["good_df_json"])

    if good_df.empty:
        print(f"[PREDICT] No good rows to predict for file: {filename}")
        return

    # Send features + Outcome (already validated)
    cols_to_send = EXPECTED_COLUMNS + ["Outcome"]
    good_df = good_df[cols_to_send]

    payload = {"data": good_df.to_dict(orient="records")}

    print(f"[PREDICT] Sending {len(good_df)} rows to /predict for file: {filename}")

    response = requests.post(PREDICT_ENDPOINT, json=payload, timeout=30)
    response.raise_for_status()
    print("[PREDICT] Response:", response.json())

# ---------------------------------------------------------------------
# DAG
# ---------------------------------------------------------------------
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="data_ingestion_pipeline",
    schedule="*/5 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    description="Read → validate → statistics → alerts → save"
) as dag:

    read_data = PythonOperator(
        task_id="read-data",
        python_callable=read_random_file,
    )

    validate_data_task = PythonOperator(
        task_id="validate-data",
        python_callable=validate_data,
    )

    save_statistics_task = PythonOperator(
        task_id="save-statistics",
        python_callable=save_statistics,
    )
    predict_task = PythonOperator(
    task_id="send-predictions",
    python_callable=send_predictions,
    )
    send_alerts_task = PythonOperator(
        task_id="send-alerts",
        python_callable=send_alerts,
    )

    save_file_task = PythonOperator(
        task_id="save-file",
        python_callable=save_file,
    )

    import os
import random
import shutil
import pandas as pd
from datetime import datetime, timedelta
import requests

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# ---------------------------------------------------------------------
# PATHS  (FINAL — DO NOT CHANGE)
# ---------------------------------------------------------------------
STATS_ENDPOINT = "http://localhost:8000/saveStatistics"
PREDICT_ENDPOINT = "http://localhost:8000/predict?source=scheduled"

# ABSOLUTE PATH TO YOUR PROJECT'S REAL DATA FOLDER
BASE_PATH = "/home/brk/projects/final_dsp_project/DSP-FINAL-PROJECT/data"

RAW_DIR = os.path.join(BASE_PATH, "raw-data")
GOOD_DIR = os.path.join(BASE_PATH, "good_data")
BAD_DIR = os.path.join(BASE_PATH, "bad_data")
REPORTS_DIR = os.path.join(BASE_PATH, "reports")

# Ensure folders exist
for d in [RAW_DIR, GOOD_DIR, BAD_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)


# Expected schema
EXPECTED_COLUMNS = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
]

EXPECTED_DTYPES = {
    "Pregnancies": "int",
    "Glucose": "int",
    "BloodPressure": "int",
    "SkinThickness": "int",
    "Insulin": "int",
    "BMI": "float",
    "DiabetesPedigreeFunction": "float",
    "Age": "int",
}

# ---------------------------------------------------------------------
# TASK 1 — READ DATA
# ---------------------------------------------------------------------
def read_random_file(**context):
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]

    if not files:
        raise ValueError("No files found in raw-data folder.")

    filename = random.choice(files)
    filepath = os.path.join(RAW_DIR, filename)

    df = pd.read_csv(filepath)

    # Delete after reading
    os.remove(filepath)

    context["ti"].xcom_push(key="filename", value=filename)
    context["ti"].xcom_push(key="dataframe", value=df.to_json())

    print(f"Read and deleted file: {filename}")


# ---------------------------------------------------------------------
# TASK 2 — VALIDATE DATA (schema + types per row)
# ---------------------------------------------------------------------
def validate_data(**context):
    df = pd.read_json(context["ti"].xcom_pull(key="dataframe"))

    errors_detected = set()
    good_rows = []
    bad_rows = []

    # 1. Column-level validation
    required_cols = EXPECTED_COLUMNS + ["Outcome"]

    # Missing columns
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        errors_detected.add("missing columns")

    # Extra columns
    extra_cols = [c for c in df.columns if c not in required_cols]
    if extra_cols:
        errors_detected.add("extra columns")

    # Wrong number of columns
    if len(df.columns) != len(required_cols):
        errors_detected.add("incorrect number of columns")

    # 2. Row-level validation
    for idx, row in df.iterrows():
        row_is_bad = False

        for col, dtype in EXPECTED_DTYPES.items():
            value = row.get(col)

            # Null or NaN
            if pd.isna(value):
                errors_detected.add("null or NaN value")
                row_is_bad = True
                continue

            # Datatype check
            try:
                if dtype == "int":
                    casted = int(value)
                elif dtype == "float":
                    casted = float(value)
            except:
                errors_detected.add("invalid datatype")
                row_is_bad = True
                continue

            if casted < 0:
                errors_detected.add("negative numeric value")
                row_is_bad = True

            if col == "Age" and not (0 <= casted <= 130):
                errors_detected.add("age out of range")
                row_is_bad = True

            if col == "Insulin" and not (0 <= casted <= 900):
                errors_detected.add("insulin out of range")
                row_is_bad = True

        outcome = row.get("Outcome")
        if pd.isna(outcome) or outcome not in [0, 1]:
            errors_detected.add("invalid outcome value")
            row_is_bad = True

        if row_is_bad:
            bad_rows.append(row)
        else:
            good_rows.append(row)

    validation_result = {
        "errors": ";".join(sorted(errors_detected)),
        "nb_rows": len(df),
        "nb_good": len(good_rows),
        "nb_bad": len(bad_rows),
        "has_errors": len(errors_detected) > 0,
        "good_df_json": pd.DataFrame(good_rows).to_json(),
        "bad_df_json": pd.DataFrame(bad_rows).to_json(),
    }

    context["ti"].xcom_push(key="validation", value=validation_result)


# ---------------------------------------------------------------------
# TASK 3 — SAVE STATISTICS
# ---------------------------------------------------------------------
def save_statistics(**context):
    validation = context["ti"].xcom_pull(key="validation")
    filename = context["ti"].xcom_pull(key="filename")

    payload = {
        "filename": filename,
        "nb_rows": validation["nb_rows"],
        "nb_valid_rows": validation["nb_good"],
        "nb_invalid_rows": validation["nb_bad"],
        "errors": validation["errors"],
        "timestamp": str(datetime.utcnow())
    }

    print("Sending statistics to API:", payload)

    try:
        response = requests.post(STATS_ENDPOINT, json=payload)
        response.raise_for_status()
        print("Statistics successfully sent:", response.json())
    except Exception as e:
        print("Error sending statistics:", str(e))
        raise


# ---------------------------------------------------------------------
# TASK 4 — SEND ALERTS + HTML REPORT
# ---------------------------------------------------------------------
def send_alerts(**context):
    validation = context["ti"].xcom_pull(key="validation")
    filename = context["ti"].xcom_pull(key="filename")

    report_path = os.path.join(REPORTS_DIR, f"{filename}_report.html")

    with open(report_path, "w") as f:
        f.write("<h1>Data Quality Report</h1>")
        f.write(f"<p>File: {filename}</p>")
        f.write(f"<p>Total Rows: {validation['nb_rows']}</p>")
        f.write(f"<p>Good Rows: {validation['nb_good']}</p>")
        f.write(f"<p>Bad Rows: {validation['nb_bad']}</p>")
        f.write(f"<p>Errors: {validation['errors']}</p>")

    print(f"Generated report: {report_path}")

    POWER_AUTOMATE_URL = (
        "https://default3534b3d7316c4bc99ede605c860f49."
        "d2.environment.api.powerplatform.com:443/powerautomate/automations/direct/"
        "workflows/86b84d99340e439a8ec7eda4788a9ecd/triggers/manual/"
        "paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig="
        "zY7ket8QdnSBVLSrRVMnBG8bcgEixVMrGKEBzW7UZLc"
    )

    if validation["has_errors"]:
        payload = {
            "filename": filename,
            "nb_rows": validation["nb_rows"],
            "nb_good": validation["nb_good"],
            "nb_bad": validation["nb_bad"],
            "errors": validation["errors"],
            "report_path": report_path,
            "alert": f"Data quality issues detected in {filename}"
        }

        try:
            response = requests.post(POWER_AUTOMATE_URL, json=payload)
            response.raise_for_status()
            print("Teams alert sent successfully")
        except Exception as e:
            print(f"Failed to send alert: {e}")

    context["ti"].xcom_push(key="report_path", value=report_path)


# ---------------------------------------------------------------------
# TASK 5 — SAVE FILE (good_data / bad_data / split)
# ---------------------------------------------------------------------
def save_file(**context):
    validation = context["ti"].xcom_pull(key="validation")
    filename = context["ti"].xcom_pull(key="filename")

    good_df = pd.read_json(validation["good_df_json"])
    bad_df = pd.read_json(validation["bad_df_json"])

    if validation["nb_bad"] == 0:
        good_df.to_csv(os.path.join(GOOD_DIR, filename), index=False)
        print(f"All rows good. Saved to good_data/{filename}")
        return

    if validation["nb_good"] == 0:
        bad_df.to_csv(os.path.join(BAD_DIR, filename), index=False)
        print(f"All rows bad. Saved to bad_data/{filename}")
        return

    good_df.to_csv(os.path.join(GOOD_DIR, f"good_{filename}"), index=False)
    bad_df.to_csv(os.path.join(BAD_DIR, f"bad_{filename}"), index=False)

    print(f"Split file saved: good_data/good_{filename}, bad_data/bad_{filename}")

def send_predictions(**context):
    validation = context["ti"].xcom_pull(key="validation")
    filename = context["ti"].xcom_pull(key="filename")

    good_df = pd.read_json(validation["good_df_json"])

    if good_df.empty:
        print(f"[PREDICT] No good rows to predict for file: {filename}")
        return

    # Send features + Outcome (already validated)
    cols_to_send = EXPECTED_COLUMNS + ["Outcome"]
    good_df = good_df[cols_to_send]

    payload = {"data": good_df.to_dict(orient="records")}

    print(f"[PREDICT] Sending {len(good_df)} rows to /predict for file: {filename}")

    response = requests.post(PREDICT_ENDPOINT, json=payload, timeout=30)
    response.raise_for_status()
    print("[PREDICT] Response:", response.json())

# ---------------------------------------------------------------------
# DAG
# ---------------------------------------------------------------------
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="data_ingestion_pipeline",
    schedule="*/5 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    description="Read → validate → statistics → alerts → save"
) as dag:

    read_data = PythonOperator(
        task_id="read-data",
        python_callable=read_random_file,
    )

    validate_data_task = PythonOperator(
        task_id="validate-data",
        python_callable=validate_data,
    )

    save_statistics_task = PythonOperator(
        task_id="save-statistics",
        python_callable=save_statistics,
    )
    
    predict_task = PythonOperator(
        task_id="send-predictions",
        python_callable=send_predictions,
    )
    
    send_alerts_task = PythonOperator(
        task_id="send-alerts",
        python_callable=send_alerts,
    )

    save_file_task = PythonOperator(
        task_id="save-file",
        python_callable=save_file,
    )

    read_data >> validate_data_task >> save_statistics_task >> predict_task >> send_alerts_task >> save_file_task
